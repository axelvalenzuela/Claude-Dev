# Deployment (intranet server)

This app was built and is tested as a local Django dev-server project. This
document covers what changed to make it deployable on a company intranet
server, and how to actually run it there. **Before this pass, none of this
existed** — no `Dockerfile`, no `STATIC_ROOT`, no production WSGI server, no
CI pipeline. All of it is new.

## Why containers, not a bare-metal install

For a small internal tool like this, running it as a container is the more
prudent choice over installing Python/Django directly on a Windows or Linux
server:

- **Reproducibility.** The image pins the exact Python version and every
  dependency (`requirements.txt`). "Works on my machine" stops being a
  question — the container that passed CI is the same one that runs on the
  server.
- **Clean updates and rollbacks.** Shipping a new version is rebuilding the
  image and restarting the container; going back is running the previous
  image tag. There's no in-place `pip install --upgrade` on a live server to
  get wrong.
- **Isolation.** The app's Python environment can't drift from — or collide
  with — whatever else IT already runs on that server.
- **No local Python install to maintain on the server itself.** Only Docker
  (or another OCI runtime) needs to be present; IT doesn't need to keep a
  Python installation patched and separately secured.

The trade-off is that whoever runs the server needs Docker available. On a
company intranet server that's normally a one-time setup, so it's a good
trade for a tool that will be redeployed more than once.

## What's in the image

- `Dockerfile`: a single-stage `python:3.12-slim` image. It installs
  `requirements.txt` (now including `gunicorn`, the production WSGI server,
  and `whitenoise`, which serves the collected static files directly from
  the app process — no separate nginx needed in front), runs
  `collectstatic` at build time, and drops to a non-root user before
  starting. On container start it applies migrations (safe to repeat — a
  no-op once the DB is current) and then starts `gunicorn`.
- `docker-compose.yml`: runs that image as a single service, publishing
  port 8000, loading secrets from a local `.env` file (never committed —
  see `.env.example`), and persisting the SQLite database and uploaded/
  generated files in a named Docker volume (`app_data`, mounted at `/data`)
  — so a rebuild or redeploy never touches real data.
- `.dockerignore`: keeps the local venv, `.env`, the dev SQLite DB, and
  local media out of the build context/image.

## Running it

1. Install Docker (and Docker Compose, which ships with modern Docker
   installs) on the target machine.
2. Copy `.env.example` to `.env` next to `docker-compose.yml` and fill in
   real values — at minimum a strong, random `DJANGO_SECRET_KEY` (the
   default in `.env.example` is a local-dev placeholder and must not be
   used anywhere reachable by anyone but you) and
   `DJANGO_ALLOWED_HOSTS` set to the server's intranet hostname/IP.
3. `docker compose up -d --build`
4. The app is now on `http://<server>:8000/`. The three seeded accounts
   from `.env` (HR admin, ICS admin, bootstrap admin) work exactly as they
   do locally — see the main `README.md` credentials table.
5. To update after a code change: `git pull && docker compose up -d --build`.
6. To back up: back up the `app_data` Docker volume (it holds the SQLite
   database and every uploaded/generated file) — e.g.
   `docker run --rm -v lab2_app_data:/data -v $(pwd):/backup alpine tar czf /backup/app_data.tar.gz -C /data .`

## HTTPS

`gunicorn` itself does not terminate TLS. Two supported options:

- **Stay on plain HTTP** for a first internal rollout — the default. Leave
  `DJANGO_HTTPS_ENABLED` unset (`False`).
- **Put a reverse proxy in front** (nginx, Caddy, or the company's existing
  intranet load balancer) that terminates TLS and forwards to port 8000,
  then set `DJANGO_HTTPS_ENABLED=True` in `.env`. This turns on
  `SECURE_SSL_REDIRECT`, secure cookies, and HSTS together (see
  `config/settings.py`) — deliberately all-or-nothing, since HSTS in front
  of plain HTTP just locks users out.

If a reverse proxy is added, also set `DJANGO_CSRF_TRUSTED_ORIGINS` to the
public URL(s) it's reached at (e.g. `https://expenses.intranet.mhp.local`).

## Database

SQLite is the default and is fine for this app's expected load (an internal
tool, not a public-facing service). If usage grows enough to need a real
database server, set `DATABASE_URL` in `.env` (django-environ syntax, e.g.
`postgres://user:pass@host:5432/dbname`) — `config/settings.py` already
reads it, no code change needed. Only a driver package (`psycopg`) would
need to be added to `requirements.txt`.

## CI pipeline

`.github/workflows/lab2-ci.yml` runs on every push/PR touching `lab2/`:
installs dependencies, runs `manage.py check`, runs the full test suite,
runs `manage.py check --deploy` under production-like settings (catches
config regressions like a forgotten env var before they reach the server),
and does a `docker build` to confirm the image still builds. It's a
starting template — the comments at the top of that file list the next
things worth adding (a linter, a dependency-vulnerability scan, pushing the
built image to a registry the server pulls from) once the team decides on
those tools.
