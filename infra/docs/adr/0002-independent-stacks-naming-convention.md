# 0002 — Independent stacks tied together by a naming convention, not heavy cross-stack imports

**Status:** Accepted

## Context

The infrastructure splits naturally into separate concerns — network,
storage, security (IAM/KMS), messaging (SQS/Lambda), compute (EC2), edge
(ALB/ACM/Route53/WAF) — and the user explicitly asked for "modulos en
folders separados" (separate module folders) rather than one giant
template. CloudFormation offers two ways for one stack to reference a
resource created by another: `Fn::ImportValue` against another stack's
`Export`, or just knowing the resource's name/ARN pattern in advance.
Cross-stack `Fn::ImportValue` has a sharp edge: AWS will not let you
delete or update an exported value while any other stack still imports
it, which turns routine changes into "find every importer first" and
can wedge an update indefinitely if two stacks end up needing to import
from each other.

## Decision

Two different mechanisms for two different needs, not one blanket rule:

1. **Real infrastructural handles that must already exist** — VPC ID,
   subnet IDs, security group IDs, the EC2 instance profile ARN — are
   passed via genuine `Fn::ImportValue`/`Export`, because there is no
   way to construct a VPC ID out of a naming pattern; it's assigned by
   AWS at creation time. These are also the exports least likely to
   churn once a stack is stood up.
2. **IAM policy documents that reference a same-account resource by
   name** (an S3 bucket ARN, a DynamoDB table ARN, an SQS queue ARN) are
   built with `Fn::Sub` against a shared `ProjectName`/`Environment`
   naming convention instead of imported — e.g.
   `arn:aws:s3:::${ProjectName}-${Environment}-reports` — because IAM
   accepts a policy statement referencing a resource that doesn't exist
   yet or was already deleted (the effect just does nothing), so this
   never blocks a stack update or forces a strict creation order.

Every template takes `ProjectName` and `Environment` as parameters with
the same defaults, so `storage.yaml` and `security.yaml` agree on the
bucket's name without either one importing the other's export.

## Alternatives considered

- **One monolithic template** — simplest mental model, directly
  contradicts the user's explicit "modulos en folders separados"
  request, and turns every small change (e.g. adjusting the WAF rule
  set) into a full-stack update touching unrelated resources.
- **`Fn::ImportValue` everywhere, including IAM policies** — the
  "obviously correct" CloudFormation-native approach, rejected because
  it creates a strict deployment order (network → storage → security →
  ...) and a strict *teardown* order in reverse, and locks any exported
  value against changes for as long as anything imports it — a bad fit
  for a project meant to be "adjusted later" by someone other than the
  original author.
- **Nested stacks** (`AWS::CloudFormation::Stack`) — keeps one
  `aws cloudformation deploy` entrypoint, but re-couples everything
  into one deployable unit and requires uploading child templates to
  S3 before the parent can reference them, adding a packaging step this
  project doesn't need yet.

## Consequences

- Deployment order still matters for the imported values (network
  before anything that needs its VPC/subnet IDs) but *not* for anything
  IAM-policy-shaped — security's IAM roles can be created before or
  after storage's S3 bucket without either template caring.
- Renaming `ProjectName` or `Environment` after first deploy changes
  every constructed ARN at once; treat those two parameters as fixed
  once a stack has been created for real.
- A typo in the naming convention (e.g. one template using `-reports`
  and another `-report`) fails silently at runtime (access denied) not
  at template-validation time — mitigated by defining the convention
  once in this ADR and by `cfn-lint` catching syntax but not semantic
  drift, so a future reviewer should grep for the literal bucket/table
  name across templates when touching naming.
