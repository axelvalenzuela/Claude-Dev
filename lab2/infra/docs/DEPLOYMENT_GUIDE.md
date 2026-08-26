# Deployment guide — what's left to actually deploy this

This is the actionable checklist behind `infra/README.md`'s short "still
to do" summary. `infra/templates/` and the ADRs in `infra/docs/adr/`
define the target AWS architecture; this document tracks the specific,
concrete steps between that scaffold and a real deploy, each one tied to
an exact file so nothing has to be rediscovered later. Check items off
as they're done — this file is meant to be edited, not just read.

Two things already existed in this project before this infrastructure work
and this guide assumes them: a working `Dockerfile` (single container,
gunicorn + WhiteNoise, `EXPOSE 8000`) and `docs/DEPLOYMENT.md`
(the existing intranet-deployment doc, in Spanish, written for a
single always-on server with a Docker volume). Everything below is
specifically about the *additional* gap between that intranet story and
the AWS architecture in `infra/templates/`.

## Done

- [x] **Health check endpoint** — the ALB target group in `edge.yaml`
  needs `HealthCheckPath` (default `/healthz`) to return 200. Added
  `config/views.py::health_check` (checks real DB connectivity, not
  just "the process is alive") and wired it at `config/urls.py`
  (`path('healthz', health_check, ...)`, unauthenticated, no trailing
  slash — matches the ALB's exact request path with no redirect).
- [x] **Port mismatch** — `network.yaml`, `compute.yaml`, and
  `edge.yaml` all defaulted `AppPort`/the security group rule to 8080;
  the real `Dockerfile` binds gunicorn to 8000. Fixed all three to 8000.
- [x] **TLS-terminating-proxy redirect loop** — `config/settings.py`
  turns on `SECURE_SSL_REDIRECT` whenever `DJANGO_HTTPS_ENABLED=True`,
  which is *always* the case when something in front of gunicorn (nginx/
  Caddy per `docs/DEPLOYMENT.md`, or the ALB in `edge.yaml`)
  terminates TLS and forwards plain HTTP. Without telling Django to
  trust `X-Forwarded-Proto`, every request looks insecure to
  `request.is_secure()` and gets redirected back to HTTPS forever — the
  proxy/ALB sends it right back over HTTP, and the ALB's health check
  fails (a redirect isn't a 200). Fixed by setting
  `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")`
  alongside the rest of the `HTTPS_ENABLED` block in `settings.py`. This
  was a latent bug in the *existing* intranet reverse-proxy story too,
  not something the ALB introduced — it just never surfaced because
  nobody had turned `DJANGO_HTTPS_ENABLED=True` on behind a real proxy
  yet.

## Still to do, in the order you'd hit them

### 1. Get the Docker image into AWS

`compute.yaml`'s EC2 instance only installs Docker Engine in its
`UserData` — it does not build or pull the app image. You need an image
registry stack (not yet written — a natural `infra/templates/registry.yaml`
would be a single `AWS::ECR::Repository`) and a CI step that runs
`docker build` + `docker push` on every merge, extending
`.github/workflows/lab2-ci.yml` (which already does a `docker build` to
confirm the image builds, per `docs/DEPLOYMENT.md`'s CI section —
it just doesn't push anywhere yet).

### 2. Get the app actually running on the instance

Once an image exists in a registry, `compute.yaml`'s `UserData` (or,
better, a systemd unit installed by `UserData`) needs to:

1. Authenticate to the registry (`aws ecr get-login-password` — the
   instance role in `security.yaml`'s `AppInstanceRole` needs
   `ecr:GetAuthorizationToken` + `ecr:BatchGetImage` added once the
   registry stack exists).
2. `docker pull` the image and run it with the same environment
   variables `docs/DEPLOYMENT.md` already documents for
   `docker-compose.yml` (`DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`,
   `DJANGO_HTTPS_ENABLED=True`, `DATABASE_URL` — see item 4 below).
3. Restart automatically on instance reboot (a systemd unit with
   `Restart=always`, not a one-shot `UserData` script that only runs
   once at boot).

This is genuinely more robust as a small AMI-baking pipeline (EC2 Image
Builder or Packer) than as a longer `UserData` script — worth deciding
before writing it, not worth guessing at here.

### 3. Wire up real secrets

Nothing in this project provisions a secrets store — deliberately, per
[ADR 0008](adr/0008-iam-roles-not-users.md)'s "no keys for now."
`DJANGO_SECRET_KEY` and the database credentials (item 4) need to come
from somewhere other than a `.env` file baked into an AMI or pasted into
`UserData` (both would leak secrets into a place other people/processes
can read). When you're ready: AWS Secrets Manager or SSM Parameter
Store (SecureString), read at container start, with
`secretsmanager:GetSecretValue`/`ssm:GetParameter` added to
`AppInstanceRole` in `security.yaml` for exactly that secret's ARN — no
broader.

### 4. Move off SQLite

[`docs/adr/0002-database-sqlite-then-postgres.md`](../../docs/adr/0002-database-sqlite-then-postgres.md)
already documents this decision and says it plainly: SQLite is fine for
a single always-on server with a persistent Docker volume, but **is a
hard requirement to leave, not just a nice-to-have, once this runs on
any cloud container/VM story** — an EC2 instance replacement (a patch,
an AMI update) has no guarantee the same EBS volume survives. No new
infrastructure decision needed here — `docs/DEPLOYMENT.md` already
says the code needs zero changes, just `psycopg[binary]` added to
`requirements.txt` and a `DATABASE_URL` env var pointed at a
managed Postgres instance. This infrastructure project does not yet
provision that Postgres instance (no `AWS::RDS::DBInstance` exists in
any template here) — add an `infra/templates/database.yaml` when you're
ready, following the same naming convention as the others
([ADR 0002](adr/0002-independent-stacks-naming-convention.md)).

### 5. Move uploaded files off local disk

`docs/DEPLOYMENT.md` also already flags this one directly: receipts
and generated Excel/Word files live under `MEDIA_ROOT` on local disk
today (fine on the intranet server's dedicated Docker volume, not safe
if the EC2 instance is ever replaced rather than just restarted). This
**is a real code change**, not just configuration — add
`django-storages` to `requirements.txt`, configure the `"default"`
entry in `STORAGES` (`config/settings.py`) to use
`storages.backends.s3.S3Storage` pointed at the bucket `storage.yaml`
already provisions (`${ProjectName}-${Environment}-reports-${AWS::AccountId}`),
toggled by an env var so local dev and the intranet Docker deployment
keep using local disk unchanged. The EC2 instance already has
`s3:PutObject`/`GetObject`/`DeleteObject` on that exact bucket via
`AppInstanceRole` in `security.yaml` — `django-storages` picks up
credentials from the instance's IAM role automatically (the whole point
of [ADR 0008](adr/0008-iam-roles-not-users.md)), no access key to
configure.

### 6. Point DNS at something real

`edge.yaml`'s `DomainName` and `HostedZoneId` parameters are
placeholders (`expenses.example-mhp.internal`, blank respectively) —
the ACM certificate won't validate and no Route53 record will be
created until these point at a domain/hosted zone you actually own.
Once you have one, redeploy `edge.yaml` with both filled in.

### 7. Schedule the file-retention cleanup job

`docs/DEPLOYMENT.md` documents `cleanup_old_documents` as a cron
job for the intranet server. On EC2, the equivalent is a systemd timer
(installed alongside the app's own systemd unit from item 2) or an
`AWS::Scheduler::Schedule` invoking a small Lambda / ECS task — either
works; pick one and add it to `compute.yaml`. Not yet done anywhere in
this infra project.

### 8. Move the WAF from COUNT to BLOCK

[ADR 0009](adr/0009-security-baseline.md) already flags this: the
managed rule groups in `edge.yaml`'s `WebAcl` are deployed with
`OverrideAction: None` (blocking), which is the end state — before
relying on it in production, temporarily switch the two managed rule
groups to `OverrideAction: {Count: {}}`, watch the WAF console's sampled
requests against real app traffic for a few days to catch false
positives (an admin form field matching a generic SQLi signature, for
example), then switch back to `None`.

### 9. Fill in real parameter files

`infra/parameters/dev.example.json` documents which output from which
stack each parameter needs. Copy it to `dev.json` (git-ignored, see
`infra/.gitignore`) and fill in real values as each stack is deployed
and its outputs become available — `infra/scripts/deploy-stack.ps1`
reads from `parameters/<environment>.json` directly.

### 10. Extend the validation Lambda's real logic

`messaging.yaml`'s `ValidationFunction` is a working skeleton — it
confirms the uploaded object exists and is non-empty, then writes a
placeholder record to DynamoDB. Before trusting its output, extend it to
mirror the real checks `expenses/pdf_analysis.py` and
`expenses/image_analysis.py` already do at upload time (amount/
date/vendor/currency extraction for PDFs, legibility/blur checks for
images) — so a file that fails those checks server-side lands in the
dead-letter queue instead of a false "validated" record.
