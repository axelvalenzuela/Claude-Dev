# 0011 — JWT-based authentication for the employee/admin web portal

**Status:** Accepted

## Context

The app was asked to move from Django's default session/cookie login to
JWT-based authentication for its web portal. The portal (everything under
`/accounts/` and `/reports/`) and the reskinned Django Admin (`/admin/`)
had shared exactly one authentication mechanism until now (ADR 0001) —
one Django project, one session/auth system, separated only by URL prefix
and `is_staff`. Replacing that mechanism for the whole app runs into a
hard constraint: `django.contrib.admin` has no supported way to
authenticate a request from anything other than Django's own session —
its login view, its permission checks, and every one of its templates
assume `request.user` was populated by `AuthenticationMiddleware` reading
`request.session`. There is no official "run Admin on a stateless token"
mode.

## Decision

Split the two by URL scope instead of unifying them:

- **The employee/admin portal** (everything except `/admin/`) now
  authenticates from a pair of signed JWTs in HttpOnly cookies —
  `accounts/jwt_auth.py`'s `JWTAuthenticationMiddleware`, inserted right
  after Django's own `AuthenticationMiddleware` in `MIDDLEWARE`, so it
  runs on every request but only overrides `request.user` for non-admin
  paths. A **short-lived access token** (15 minutes by default) proves
  identity on each request without a database round trip beyond looking
  the user up by id; a **longer-lived refresh token** (7 days by default)
  silently mints a new access token once the old one expires, so the
  portal doesn't visibly log someone out every 15 minutes. Both are set
  by `accounts/views.py:JWTLoginView` and `SignUpView` on success, and
  cleared by `JWTLogoutView`, which also blacklists the refresh token
  (`accounts/models.py:BlacklistedToken`) — the only way to make a
  specific JWT stop working before its own `exp`, since a JWT is
  otherwise valid until it expires regardless of anything the server does
  afterward.
- **Django Admin** (`/admin/`) keeps its existing session-based login
  exactly as before — untouched, unaffected, still using
  `AdminLoginForm`/`AdminAuthenticationForm` and Django's own session
  machinery. `JWTAuthenticationMiddleware` explicitly skips any path
  starting with `/admin/`.
- `django.contrib.auth`'s own `login_required`/`LoginRequiredMixin`
  (used throughout `expenses/`) needed **zero changes** — they only ever
  check `request.user.is_authenticated`, and don't care whether that
  `User` instance came from a session or from
  `JWTAuthenticationMiddleware` overriding it from a cookie.
- `SessionMiddleware` stays in `MIDDLEWARE` project-wide — Admin still
  needs it, and so does Django's messages framework (flash messages are
  session-backed by default) even on portal pages that no longer use the
  session for *authentication*.

## Alternatives considered

- **Move Admin to JWT too, for one unified mechanism**: rejected outright
  — not supported by `django.contrib.admin` without replacing large
  parts of it, which would have meant giving up the reskinned Admin this
  app is built around (ADR 0001) for a login mechanism, not gaining
  anything the portal's own JWT doesn't already provide.
- **`Authorization: Bearer <token>` header instead of a cookie**: the
  standard approach for an API client, but this is a server-rendered app
  navigated by clicking links and submitting HTML forms — there is no
  JavaScript layer already attaching a header to every request, and
  building one just to carry a token that a cookie already delivers
  automatically would be solving a problem this app doesn't have.
  HttpOnly cookies were chosen specifically so the token is inaccessible
  to any JavaScript running on the page (mitigating XSS), at the cost of
  being sent automatically to any request Django itself must handle CSRF
  protection for — already true of the session cookie it replaces, so no
  new protection needed there.
- **`djangorestframework-simplejwt`**: the standard JWT library for
  Django, but built around Django REST Framework's request/response
  cycle and `Authorization` headers — this app has no DRF and no REST
  API, so adopting it would mean pulling in a framework for the one
  feature (JWT encode/decode) that a five-function module on top of
  plain `PyJWT` already provides.
- **No refresh token, only a long-lived access token**: simpler (one
  cookie, no silent-refresh logic), but means a single leaked token stays
  valid for as long as the whole session should last, with no way to
  shorten that exposure window without also shortening how long someone
  can stay logged in. The access/refresh split keeps the token that's
  actually checked on every request short-lived, while letting a real
  session last days.

## Consequences

- **A stolen access token is valid until it expires** (15 minutes by
  default) — there is no way to revoke a single access token early, only
  its refresh token. This is the deliberate trade-off of not blacklisting
  access tokens individually (which would require a database check on
  every single request, defeating the point of a stateless access
  token) — 15 minutes was chosen as short enough that this window is
  acceptable for an internal tool.
- **Changing `JWT_SECRET_KEY` invalidates every outstanding token at
  once** — the closest this design gets to a global "log everyone out"
  switch, useful in an incident but with no more granularity than that.
- **The existing test suite's `Client.login()`/`force_login()` calls
  needed no changes** — those helpers create a session directly, and
  `JWTAuthenticationMiddleware` only overrides `request.user` when a JWT
  cookie is actually present, leaving session-derived authentication
  alone otherwise. The one test that did need adjusting
  (`test_two_signups_get_different_numbers` in
  `accounts/tests/test_signup.py`) called `self.client.logout()` between
  two signups, which clears session state but not the JWT cookies the
  first signup had set — the fix was an explicit
  `self.client.cookies.clear()`, documented inline.
- **`accounts/management/commands/cleanup_expired_tokens.py`** needs
  scheduling (cron/Task Scheduler) alongside the existing
  `cleanup_old_documents`, per `docs/DEPLOYMENT.md`, or `BlacklistedToken`
  rows accumulate indefinitely — they're only ever pruned by this command,
  never automatically.
- `docs/ARCHITECTURE.md`'s "same session/auth system" claim (written
  under ADR 0001, before this decision) is no longer accurate for the
  portal vs. Admin and has been corrected alongside this ADR.
