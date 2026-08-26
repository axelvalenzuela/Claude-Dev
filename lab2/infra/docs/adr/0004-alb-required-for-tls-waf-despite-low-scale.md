# 0004 — An Application Load Balancer despite low scale — required for ACM/WAF/Route53, not for load balancing

**Status:** Accepted

## Context

The user's message contains what reads like a contradiction: "no creo
necesitar algo tan elaborado como un balanceador... pero hazlo por
buenas practicas" (I don't think I need something as elaborate as a load
balancer, but do it anyway per best practices), immediately followed by
asking for a Route53 DNS record, an ACM certificate, and WAF. Those
three requirements are not actually independent of the load-balancer
question: **AWS Certificate Manager certificates and AWS WAF Web ACLs
cannot be attached directly to a bare EC2 instance.** They attach to a
small, fixed set of resource types — for HTTP(S) traffic, that means an
Application Load Balancer, a CloudFront distribution, or API Gateway.
There is no way to give a lone EC2 instance a browser-trusted TLS
certificate or a WAF rule set in front of it without inserting one of
those.

## Decision

Include a minimal single-target-group Application Load Balancer,
specifically as the attachment point for the ACM certificate and the
WAF Web ACL, with Route53 pointing an A/ALIAS record at the ALB rather
than at the instance. This resolves the apparent contradiction: the ALB
here is not being added *for load balancing* (there is exactly one
target and no scaling policy — see ADR 0003) — it is the mandatory
infrastructural adapter that lets a single EC2 instance have a real
certificate and a WAF in front of it, which is what the user actually
asked for.

## Alternatives considered

- **CloudFront in front of the EC2 instance instead of an ALB** — also
  supports ACM and WAF, and adds edge caching/global distribution. Rejected
  for this app: it's an authenticated internal tool with no meaningfully
  cacheable public content, so CloudFront's main benefit doesn't apply,
  and it adds another distinct service (with its own origin-access and
  cache-behavior configuration) for no gain over an ALB here.
- **Bare EC2 with a self-signed or Let's Encrypt certificate installed
  on the box, no WAF** — technically simpler, but drops two of the
  user's explicit requirements (a real ACM-issued certificate, WAF) and
  pushes certificate renewal onto the instance itself instead of AWS
  managing it. Rejected.
- **API Gateway + VPC Link to the EC2 instance** — also gets ACM/WAF, but
  is built for API-shaped traffic (Lambda/HTTP APIs), not a server-
  rendered Django app with sessions and cookies; adds complexity with no
  benefit over an ALB for this workload. Rejected.

## Consequences

- One extra billed resource (the ALB) exists purely to satisfy
  ACM/WAF/Route53 attachment, not to distribute load — worth calling out
  explicitly to whoever reviews the AWS bill later so it isn't mistaken
  for premature scaling.
- The target group's health check becomes the de facto uptime check for
  the whole app; it must point at a real health endpoint on the Django
  app (documented as a follow-up in `infra/README.md`, since the app
  doesn't currently expose one).
- If the instance in ADR 0003 is ever replaced with an Auto Scaling
  group, this ALB needs no structural change — it was already built to
  front a target group, not a single hardcoded instance.
