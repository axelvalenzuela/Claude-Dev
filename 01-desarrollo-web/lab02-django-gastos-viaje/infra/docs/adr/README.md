# Architecture Decision Records — infrastructure

Same format and purpose as `docs/adr/`: one decision per file, with
the context that forced it, the alternatives that lost, and the
consequences (including the ones that aren't purely positive). These
records exist because this infrastructure was designed before an AWS
account, region, or domain name was chosen — every non-obvious choice
here needs to survive being read by someone who fills those in later,
possibly not the person who wrote this.

| # | Title | Status |
|---|---|---|
| [0001](0001-cloudformation-over-terraform.md) | CloudFormation over Terraform | Accepted |
| [0002](0002-independent-stacks-naming-convention.md) | Independent stacks tied together by a naming convention, not heavy cross-stack imports | Accepted |
| [0003](0003-single-instance-ec2-not-autoscaling.md) | A single EC2 instance, not an Auto Scaling group | Accepted |
| [0004](0004-alb-required-for-tls-waf-despite-low-scale.md) | An Application Load Balancer despite low scale — required for ACM/WAF/Route53, not for load balancing | Accepted |
| [0005](0005-private-subnet-ec2-with-s3-gateway-endpoint.md) | EC2 in a private subnet, reaching S3 through a Gateway VPC Endpoint | Accepted |
| [0006](0006-async-validation-pipeline.md) | S3 → SQS → Lambda → DynamoDB as an asynchronous validation pipeline | Accepted |
| [0007](0007-dual-datastore-split.md) | Two datastores on purpose: the app's local database for accounts, DynamoDB for validated report data | Accepted |
| [0008](0008-iam-roles-not-users.md) | IAM roles everywhere, no IAM users or long-lived access keys | Accepted |
| [0009](0009-security-baseline.md) | The security baseline: encryption, WAF, IMDSv2, least privilege | Accepted |

## Format

- **Status**: `Proposed`, `Accepted`, `Superseded by NNNN`, or `Deprecated`.
- **Context**: the problem/constraint that made a decision necessary.
- **Decision**: what was actually chosen, in one or two sentences.
- **Alternatives considered**: what else was on the table, and why it lost.
- **Consequences**: what this decision costs, not just what it buys.
