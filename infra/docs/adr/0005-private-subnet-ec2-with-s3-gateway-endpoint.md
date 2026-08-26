# 0005 — EC2 in a private subnet, reaching S3 through a Gateway VPC Endpoint

**Status:** Accepted

## Context

The user specifically asked for "una EC2 con gateway endpoint y la red
en VPC," i.e. an EC2 instance, a VPC network, and a gateway endpoint,
explicitly named as parts of the same request. The app instance needs to
read/write the S3 bucket that holds uploaded trip-report files, but
should not otherwise need unrestricted outbound internet access, and
should not be reachable directly from the internet — all inbound traffic
should come through the ALB (ADR 0004).

## Decision

The EC2 instance lives in a private subnet (no public IP, no route to
an Internet Gateway). Two subnet tiers exist, each duplicated across two
Availability Zones for the VPC's own resilience even though compute
itself is single-instance (ADR 0003): a **public** tier holding the ALB
and the NAT Gateway, and a **private** tier holding the EC2 instance. An
**S3 Gateway VPC Endpoint** is attached to the private route table so
the instance can reach the S3 bucket over AWS's internal network — no
NAT, no public internet — for its normal upload/download traffic. A
single NAT Gateway (one AZ, not one per AZ) provides the private
subnet's remaining outbound path, for cases the S3 endpoint doesn't
cover (OS/package updates, any other AWS API the instance calls that
isn't S3).

## Alternatives considered

- **Public subnet EC2 with a security group restricting inbound to the
  ALB only** — cheaper (no NAT Gateway), but leaves the instance
  theoretically addressable if a security group is ever misconfigured,
  and doesn't use the gateway endpoint the user explicitly asked for
  since a public-subnet instance can just reach S3 over the public
  internet already. Rejected: contradicts the explicit ask and weakens
  the network boundary for no real gain.
- **NAT Gateway per Availability Zone (one each)** — the AWS-recommended
  high-availability pattern, but doubles NAT Gateway cost (~$32/month
  each, plus data processing) for an internal tool with a single EC2
  instance that isn't itself HA. Rejected as disproportionate to actual
  scale; documented here as the known, deliberate cost/HA tradeoff so a
  future reviewer doesn't mistake it for an oversight.
- **VPC Interface Endpoints for every AWS service the app touches (S3,
  SQS, DynamoDB, etc.) instead of a NAT Gateway at all** — would remove
  the NAT Gateway entirely, but Interface Endpoints are billed per-
  endpoint-per-AZ regardless of traffic, which for this app's volume
  costs more than the single NAT Gateway it would replace. The S3
  Gateway Endpoint is used anyway because Gateway Endpoints are free and
  S3 is the highest-traffic dependency (every uploaded file); the
  remaining AWS-API calls stay on the NAT path rather than paying for
  more endpoints to remove a NAT Gateway that's needed for OS updates
  regardless.

## Consequences

- Only one NAT Gateway exists — if its Availability Zone has an outage,
  the private subnet's non-S3 outbound path (not S3 itself, which stays
  reachable through the endpoint in every AZ) goes down until AWS
  recovers that AZ. Acceptable for this app's stated scale; called out
  here so it isn't silently assumed to be multi-AZ-resilient.
- S3 traffic specifically never touches the NAT Gateway or incurs its
  per-GB data processing charge, regardless of which AZ the instance is
  in, because the Gateway Endpoint is associated with both AZs' private
  route tables.
- The instance has no public IP by design — reaching it for
  troubleshooting must go through AWS Systems Manager Session Manager
  (see ADR 0008), not SSH from the internet.
