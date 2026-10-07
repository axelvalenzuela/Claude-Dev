# 0008 — IAM roles everywhere, no IAM users or long-lived access keys

**Status:** Accepted

## Context

The user's request was explicit and non-negotiable: "RBAC ni llaves de
momento" (role-based access control, no keys for now) — driven by not
having a staging/account setup yet, and, independent of that, a sound
default regardless of account maturity: long-lived IAM access keys are a
standing credential-leak risk (committed to a repo, left in a shell
history, embedded in an AMI) that a role-based design avoids entirely by
never creating a static secret in the first place.

## Decision

Every piece of compute in this project authenticates as an **IAM role**,
never an IAM user with access keys:

- The **EC2 instance** gets an **instance profile** attached at launch,
  granting exactly the S3/permissions it needs (put/get objects in the
  reports bucket) — no credentials are ever stored on the box; the
  instance metadata service hands out short-lived, auto-rotating
  credentials to the SDK the Django app uses.
- **Remote access to the instance** is via **AWS Systems Manager Session
  Manager**, not SSH — this needs no key pair at all (directly
  satisfying "ni llaves" literally, not just for AWS API calls but for
  interactive access too), no inbound port 22 in any security group, and
  every session is logged to CloudWatch Logs for audit, which a
  key-pair-based SSH session wouldn't give for free.
- The **Lambda function** runs under its own execution role, scoped to
  exactly the S3/SQS/DynamoDB actions ADR 0006 describes — nothing
  broader, and specifically no `iam:*` or wildcard-resource statements.
- No `AWS::IAM::User`, `AWS::IAM::AccessKey`, or `AWS::IAM::Group`
  resource exists anywhere in these templates.

## Alternatives considered

- **An IAM user with an access key, stored in an environment variable or
  `.env` file on the instance** — the most common shortcut for "just get
  it working," and exactly what the user asked to avoid. Rejected
  outright per explicit instruction, and would have been a weaker
  default regardless.
- **SSH key pair for instance access, with the private key held by the
  operator** — the traditional EC2 access pattern, but requires
  distributing and protecting a private key file, opening port 22
  somewhere (even if restricted to a bastion), and gives no built-in
  session audit trail. Session Manager replaces this with no
  degradation in capability for this app's needs (shell access for
  troubleshooting/deploys).

## Consequences

- Nobody can `aws configure` a static credential to act as this app from
  their laptop — any local testing against real AWS resources needs its
  own separate role/credential story (e.g. an operator's own SSO role),
  which is out of scope for this infrastructure baseline and left as a
  deliberate gap for the user to fill in once they have an actual AWS
  account/SSO setup.
- Session Manager requires the SSM Agent running on the instance (bundled
  in Amazon Linux 2023 AMIs by default) and the instance's outbound path
  to the `ssm`, `ssmmessages`, and `ec2messages` endpoints — reachable
  here via the NAT Gateway (ADR 0005); an air-gapped private subnet with
  no NAT would need SSM VPC Interface Endpoints instead, which is a
  documented but not-yet-built follow-up if the NAT Gateway is ever
  removed.
- Every role's policy is written as specific actions against specific,
  name-convention-constructed ARNs (ADR 0002) rather than
  `Action: "*"`/`Resource: "*"` — reviewing any one role's YAML is
  sufficient to know exactly what it can and can't do, with no implicit
  trust boundary to reason about separately.
