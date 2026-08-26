# 0001 — CloudFormation over Terraform

**Status:** Accepted

## Context

This app needs to move from "runs on a laptop with SQLite" to a
real AWS deployment. Two mainstream ways to describe that infrastructure
as code: AWS CloudFormation (native, YAML/JSON) or Terraform (HashiCorp,
HCL, multi-cloud). No AWS account, region, or IAM setup exists yet — this
has to be written and validated with nothing but a text editor and a
linter, months before anyone runs `deploy`.

## Decision

Use CloudFormation. Every resource in this project (`infra/templates/`)
is AWS-only; there is no multi-cloud requirement now or on the horizon,
so Terraform's main advantage — one tool across providers — buys nothing
here. CloudFormation also needs no extra binary or state backend: no
Terraform state file to store in S3 with its own locking table before
the "real" infrastructure can even be created, no provider plugin
versions to pin. `cfn-lint` validates templates offline, which matches
"no AWS account yet" exactly.

## Alternatives considered

- **Terraform** — more popular, better multi-cloud story, but adds a
  state-management problem (where does `terraform.tfstate` live, who
  locks it) that doesn't exist with CloudFormation, where AWS itself
  tracks stack state. Rejected: solving a multi-cloud problem this
  project doesn't have, at the cost of a real problem (state storage)
  it would then have.
- **AWS CDK** — real programming language, more expressive, but compiles
  down to CloudFormation anyway and adds a Node/Python build toolchain
  on top of the templates. Rejected for this project's size: the extra
  abstraction layer isn't worth it for roughly a dozen resources.
- **Manual console clicking** — explicitly what the user is trying to
  avoid; not reproducible, not reviewable in git, not the point of this
  exercise.

## Consequences

- Every resource change goes through `aws cloudformation deploy` (or the
  console's "Create stack from template" import, for a first apply) —
  no `terraform plan`/`apply` two-step, but also no separate state
  backend to provision first.
- YAML verbosity is real; templates lean on `Parameters` and a shared
  naming convention (ADR 0002) to stay manageable without a templating
  language of their own.
- Anyone who later wants multi-cloud has to rewrite, not just re-target
  a provider block. Judged acceptable — nothing about this app suggests
  that will ever be needed.
