# 0003 — Single-container deployment for the intranet; cloud requires added infrastructure

**Status:** Accepted

## Context

The app needs to run somewhere other than a developer's machine — the
company's intranet was the first real target, with a cloud provider
(Azure/AWS/GCP) a plausible later target. Before this work, none of this
existed: no `Dockerfile`, no `STATIC_ROOT`, no production WSGI server, no
CI pipeline.

## Decision

**One container, one process** (`gunicorn` serving Django, with
WhiteNoise serving static files from inside the same process — no
separate nginx or app-server split) for the intranet deployment, backed
by **one named Docker volume** holding both the SQLite database file and
`media/` (uploaded receipts, generated Excel/Word). TLS is optional and
external (a reverse proxy in front, or none at all for a first internal
rollout).

For a cloud provider, this same image is the starting point, but two of
this design's assumptions stop holding (see ADR 0002 for the database
half): the single shared volume for media storage doesn't have a direct
equivalent on most managed container platforms, which typically assume
ephemeral or non-shared local disk. `docs/DEPLOYMENT.md`'s cloud section
documents what has to change (managed Postgres, object storage for
`media/`, a secrets manager) rather than this ADR re-deriving it.

## Alternatives considered

- **nginx + gunicorn as two containers**: the standard production
  pattern, but unnecessary here — WhiteNoise serves this app's small,
  infrequently-changing static asset set (vendored Bootstrap, one CSS
  file) efficiently enough from inside the same process, and skipping a
  second container removes an entire piece of infrastructure (and a
  second thing that can misconfigure) for no real benefit at this scale.
- **Deploying without containers** (a bare Python install on the
  server): rejected for reproducibility — a container image pins the
  exact Python version and every dependency; "works on my machine"
  becomes structurally impossible to hit in production, and
  updates/rollbacks become "build and run a new image" instead of a
  partial `pip install --upgrade` on a live server.

## Consequences

- Standing the intranet deployment up is `docker compose up -d --build`
  plus a `.env` file — no separate database server or static-file server
  to provision.
- The single shared volume is the one thing every backup and every
  redeploy must handle correctly (see `docs/DEPLOYMENT.md`'s backup
  command) — losing it loses the database and every generated file at
  once, with no independent recovery path for either.
- This design does **not** carry over to a cloud container platform
  as-is: it was never meant to. Treat the intranet Dockerfile as the
  reusable part and the volume-backed single-instance assumption as the
  part that needs replacing (managed DB + object storage) before
  deploying to Azure/AWS/GCP for real, rather than assuming "it's
  containerized, so it's already cloud-ready."
