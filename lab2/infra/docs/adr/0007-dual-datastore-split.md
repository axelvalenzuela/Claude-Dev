# 0007 — Two datastores on purpose: the app's local database for accounts, DynamoDB for validated report data

**Status:** Accepted

## Context

The user was explicit and specific on this point: "la app guarde en
local los usuarios administradores registrados en el portal" (the app
should keep its registered admin/portal users in its own local
database), while the Lambda-validated report data goes into DynamoDB.
This is a deliberate split, not an oversight to be "fixed" by moving
everything into one store later.

## Decision

- **Accounts, admin/supervisor roster, sessions, permissions** — stay
  exactly where they are today: the Django app's own relational database
  (`config/settings.py`'s `DATABASES`, SQLite by default per
  [`docs/adr/0002-database-sqlite-then-postgres.md`](../../docs/adr/0002-database-sqlite-then-postgres.md)
  — a different ADR series from this infra project's own numbering),
  upgradeable to RDS later without anything in this infra project
  needing to change, since that's an application-level decision. This
  infrastructure project does not provision a database for user
  accounts at all.
- **Validated report data** produced by the async pipeline (ADR 0006)
  goes into a DynamoDB table, keyed by a report identifier, because it's
  write-heavy from an event-driven Lambda, doesn't need relational joins
  against the user table, and DynamoDB's `PAY_PER_REQUEST` billing mode
  fits this app's small and unpredictable traffic without pre-
  provisioning read/write capacity.

## Alternatives considered

- **One database for everything (RDS, holding both users and reports)**
  — the more conventional enterprise default, and simpler to reason
  about with a single store. Rejected because it directly contradicts
  what the user asked for, and because it would mean the Lambda's
  execution role needs network access into a VPC-bound RDS instance
  (a Lambda-in-VPC configuration with its own ENI/cold-start
  considerations) instead of a plain AWS-API call to DynamoDB from
  outside the VPC — see ADR 0006's choice to keep the Lambda VPC-free.
- **Move user accounts into DynamoDB too, for a single-datastore
  design** — technically buildable (a single-table DynamoDB design is a
  well-known enterprise pattern), but the user asked for the opposite,
  and Django's built-in auth/permissions/session machinery is already
  built around a relational `User` model — moving it to DynamoDB would
  mean replacing Django's auth backend, a much larger and riskier change
  than this infrastructure request asked for.

## Consequences

- There is no single query that joins "this report" to "its submitting
  employee's full account record" across both stores at the database
  level — any such view has to be assembled in the application layer
  (the Django app already does this today for its own local report
  model; the DynamoDB-held validated-report data would need the same
  treatment if the app is later extended to read it back).
- Two different backup/retention policies apply: the local database
  follows whatever backup story the app's hosting already has (e.g. RDS
  automated snapshots, if/when it moves off SQLite), while DynamoDB gets
  its own point-in-time recovery setting, configured independently in
  `storage.yaml`.
- If the app is ever rearchitected to be fully event-driven (no
  synchronous EC2 backend at all), this split means the user/auth side
  would need its own separate migration story — it does not travel "for
  free" with any DynamoDB-centric redesign of the reports side.
