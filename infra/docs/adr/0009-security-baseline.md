# 0009 — The security baseline: encryption, WAF, IMDSv2, least privilege

**Status:** Accepted

## Context

The user asked that this infrastructure "pase por todos los estandares
de seguridad" (pass every security standard). That's not a single
checkbox — it's a set of independent defaults that are each cheap to
apply from the start and expensive to retrofit later. This ADR collects
the baseline decisions that don't each warrant their own record.

## Decision

- **Encryption at rest everywhere data lands**: the S3 bucket uses
  `AES256` (`SSE-S3`) default encryption with `BucketKeyEnabled` for
  cost efficiency; the DynamoDB table uses AWS-owned encryption at rest
  (the DynamoDB default); EBS volumes on the EC2 instance are encrypted
  by default at the launch-template level.
- **S3 bucket hardening**: `PublicAccessBlockConfiguration` set to block
  all four public-access vectors, bucket versioning enabled (so an
  accidental overwrite/delete of an uploaded report file is
  recoverable), and a bucket policy denying any request that isn't
  `aws:SecureTransport` (i.e. rejects plain HTTP).
- **IMDSv2 required, not just available**, on the EC2 launch template
  (`HttpTokens: required`) — closes the SSRF-to-instance-credentials
  path that IMDSv1 leaves open by default.
- **Security groups scoped to their actual traffic**: the ALB's security
  group allows inbound 443 (and 80, redirecting to 443) from the
  internet; the EC2 instance's security group allows inbound only from
  the ALB's security group (referenced by ID, not by CIDR) on the app
  port; nothing allows unrestricted inbound from `0.0.0.0/0` to the
  instance itself.
- **WAF Web ACL** attached to the ALB (ADR 0004) using AWS Managed Rule
  Groups — `AWSManagedRulesCommonRuleSet` (the OWASP-style baseline) and
  `AWSManagedRulesKnownBadInputsRuleSet` — plus a rate-based rule capping
  requests per IP, rather than hand-written WAF rules, so the rule
  content is maintained by AWS rather than by hand.
- **TLS only**: the ALB listener terminates TLS 1.2+ using the ACM
  certificate (ADR 0004); the HTTP listener exists only to issue a
  redirect to HTTPS, never to serve the app directly.
- **CloudWatch Logs everywhere there's something to log**: VPC Flow Logs
  for the VPC, ALB access logs to S3, Lambda logs (automatic), and
  Session Manager session logs (ADR 0008) — so a security review has an
  actual audit trail to look at, not just a well-configured-on-paper
  stack.

## Alternatives considered

- **AWS Config + Security Hub for continuous compliance scanning** — a
  genuinely enterprise-grade addition, but it's an ongoing service with
  its own monthly cost and its own findings to triage, which is a
  process commitment beyond "define good infrastructure defaults."
  Left as a suggested follow-up in `infra/README.md` rather than built
  in, since it's an operational practice more than a template resource.
- **Custom, hand-written WAF rules instead of AWS Managed Rule Groups** —
  more tailored, but requires someone to keep the ruleset current
  against new attack patterns; Managed Rule Groups get that maintenance
  from AWS for a small additional charge. Rejected in favor of the
  managed option for a project without a dedicated security team.
- **VPC Flow Logs to CloudWatch Logs vs. S3** — CloudWatch Logs chosen
  for easier ad hoc querying (Logs Insights) at this log volume; S3
  would be cheaper at much higher volume, which this app's traffic
  doesn't reach.

## Consequences

- Every one of these defaults is a parameter or a fixed resource
  property in the templates, not a manual post-deployment console step
  — so "secure by default" survives a from-scratch `deploy`, not just
  the first one someone remembers to click through.
- AWS Managed Rule Groups occasionally produce false positives against
  legitimate app traffic (e.g. a Django admin form with an unusual
  field name matching a generic SQLi pattern); the WAF is deployed in
  `COUNT` mode for new rule groups long enough to review sampled
  requests before switching to `BLOCK`, documented as an operational
  step in `infra/README.md` rather than hardcoded into the template.
- This baseline is a floor, not a ceiling — AWS Config/Security Hub,
  GuardDuty, and a formal WAF logging pipeline to a SIEM are all
  reasonable next steps once this app has a real user base and an owner
  who monitors it, but are out of scope for the initial baseline.
