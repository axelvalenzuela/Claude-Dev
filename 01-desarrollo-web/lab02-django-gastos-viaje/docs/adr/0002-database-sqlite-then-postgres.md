# 0002 — SQLite for intranet/dev, PostgreSQL for cloud or high concurrency

**Status:** Accepted

## Context

The app needs a relational database (structured data, real relationships
between reports/documents/users/audit entries, transactional writes on
approval). It needs to run with zero setup on a developer's machine, on
an intranet server as a single always-on container, and — potentially —
on a cloud container platform (Azure/AWS/GCP) where the app might run as
more than one instance and where local disk isn't reliably persistent or
shared between instances.

## Decision

**SQLite by default** (`config/settings.py`'s `DATABASES` reads
`DATABASE_URL` via django-environ, defaulting to a local `db.sqlite3`
file) for local development and for the documented intranet deployment
(`docs/DEPLOYMENT.md`) — a single file inside the container's persistent
volume, no separate database service to run, back up, or patch.

**PostgreSQL, via `DATABASE_URL`, for anything beyond that**: real
concurrent-write load, an existing corporate database server the company
wants used instead, or — this is the one that isn't optional — **any
deployment to a cloud container platform**. No application code changes
either way; only `DATABASE_URL` and installing the `psycopg` driver.

## Alternatives considered

- **PostgreSQL everywhere, including local dev**: would mean every
  contributor needs a running Postgres instance (or Docker) just to run
  `manage.py test`, for an app whose actual concurrency needs at this
  size don't require it. Rejected — the friction isn't worth it for an
  internal tool at this traffic level.
- **SQLite everywhere, including the cloud**: the pragmatic-but-wrong
  choice. On a single, always-on intranet container with one attached
  volume, SQLite's real limitation (one writer at a time) never becomes
  visible at this app's usage level. On most managed cloud container
  platforms, the filesystem is ephemeral or not shared across instances
  — a redeploy, a restart, or scaling to 2+ instances can lose or
  corrupt the database file outright. This isn't a performance trade-off
  at that point, it's a correctness/durability one. Rejected for any
  cloud deployment specifically because of that, not because of
  concurrency.

## Consequences

- Zero-friction local development and a genuinely simple intranet
  deployment (`docs/DEPLOYMENT.md`'s single-container setup) — no
  database server to provision, secure, or back up separately from the
  app's own volume.
- The `psycopg` driver is **not** in `requirements.txt` by default (the
  default path is SQLite) — it must be added explicitly before pointing
  `DATABASE_URL` at Postgres. Documented in `docs/DEPLOYMENT.md`, easy to
  forget if this ADR isn't read first.
- Migrating from SQLite to Postgres mid-project means a real data
  migration (`dumpdata`/`loaddata` or equivalent), not just an env var
  flip, if there's existing data to carry over — the env var flip only
  applies cleanly to a fresh database.
- Anyone deploying this app to Azure/AWS/GCP must treat the Postgres
  switch as a prerequisite, not an optional tuning step — see
  `docs/DEPLOYMENT.md`'s "Desplegar en un proveedor de nube" section.
