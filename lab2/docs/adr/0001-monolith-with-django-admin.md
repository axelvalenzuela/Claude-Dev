# 0001 — Monolithic Django app, Django Admin as the approval interface

**Status:** Accepted

## Context

The app needs two very different-looking screens: an employee-facing
portal (submit a report, upload receipts, track status) and an
admin-facing approval interface (review, approve/reject, download
exports, manage accounts). It also needs to be built and maintained by a
small team (in practice, one developer at a time) for an internal
audience of a few dozen people at most — not a public product with
independent scaling needs per surface.

## Decision

One Django project (`config/`), two apps (`accounts`, `expenses`), one
database, one deployable unit. The admin-facing surface is **Django
Admin, reshaped** — not a hand-built admin dashboard, not a separate SPA
talking to a JSON API. Every customization (the Dashboard tabs, the
Summary tab on a report's review page, the Policies/Help tabs) extends
Django Admin's own template blocks and hooks (`ModelAdmin.get_urls()`,
template block overrides, context processors) rather than replacing it.
See `docs/ARCHITECTURE.md` for how, concretely.

## Alternatives considered

- **A separate admin SPA (React/Vue) behind a DRF API**: would have
  meant building and maintaining authentication, permissions, forms, and
  CRUD screens that Django Admin already provides for free — for an
  audience of 4 admin accounts. The added surface area (a second
  frontend, a second build pipeline, CORS/API-versioning concerns) buys
  nothing this app's actual requirements need.
- **Splitting into separate services** (e.g. an "exports" microservice
  for Excel/Word generation): no independent scaling or deployment need
  exists for any part of this app — a microservices split here would add
  network calls and operational complexity to solve a scaling problem
  that doesn't exist at this traffic level.

## Consequences

- Fast to build and change: a new admin screen is a template override
  and a context processor, not a new API endpoint plus new frontend
  code.
- The admin UI is constrained by what Django Admin's template blocks
  make reasonably overridable — some things (see
  `templates/admin/expenses/expensereport/change_form_object_tools.html`)
  require knowing Django Admin's internals (e.g. `InclusionAdminNode`'s
  per-model template resolution) rather than being simple to customize
  from scratch.
- One process serving both surfaces means one deployment, one set of
  logs, one place a bug can affect both — acceptable here since both
  surfaces share the same data and the same low-traffic profile, but
  would stop being acceptable if either surface ever needed independent
  scaling or a separate release cadence.
