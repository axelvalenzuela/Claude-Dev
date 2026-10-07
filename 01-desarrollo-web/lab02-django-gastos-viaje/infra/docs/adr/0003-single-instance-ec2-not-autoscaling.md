# 0003 — A single EC2 instance, not an Auto Scaling group

**Status:** Accepted

## Context

The app serves an internal expense-report portal for well under 100
users. The user explicitly said they don't think they need something as
elaborate as a load balancer at this scale, while also asking that
everything be built "por buenas practicas" (by best practices) so it's
easy to grow into later.

## Decision

Run the Django app on a single EC2 instance in a private subnet, sized
modestly (`t3.small` default, parameterized), rather than an Auto
Scaling group. An ALB still sits in front of it (ADR 0004), pointed at a
target group with exactly one registered instance — that costs nothing
extra to leave in place and means growing to an ASG later is a target
group and launch template change, not a network redesign.

## Alternatives considered

- **Auto Scaling group from day one** — the textbook "best practice" for
  a public-facing service, but for <100 known internal users it adds an
  AMI/launch-template pipeline and multi-instance session/state concerns
  (this Django app currently assumes a single local SQLite-style
  filesystem for uploaded files during processing) with no present
  benefit. Rejected as premature for the stated scale.
- **AWS Elastic Beanstalk / App Runner** — less infrastructure to write
  by hand, but hides the VPC/IAM wiring the user explicitly asked to see
  and control ("para hacer cambios y ajustarlos yo despues"). Rejected:
  the point of this exercise is an explicit, editable IaC baseline.
- **No load balancer, EC2 with a public IP and Elastic IP + Route53
  A-record directly** — simpler, but see ADR 0004: ACM certificates and
  WAF cannot attach to a bare EC2 instance, and the user asked for both.

## Consequences

- A single instance is a single point of failure — acceptable for an
  internal tool at this scale, and explicitly the tradeoff the user
  asked for, but should be revisited if this ever becomes customer-
  facing or grows past roughly 100 concurrent users.
- Deploys to the instance (new app code) are out of scope for this
  infrastructure baseline — this stack provisions the box and its
  network/security context, not a CI/CD pipeline onto it. Left as a
  deliberately open follow-up, noted in `infra/README.md`.
- Moving to an Auto Scaling group later only requires changing the
  compute template's launch template/ASG resources and confirming the
  app can run more than one instance concurrently (shared session/file
  storage) — it does not require touching network, storage, or edge.
