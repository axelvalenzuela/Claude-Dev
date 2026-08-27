# Architecture Decision Records

Each file here records one architectural decision made on this project:
the context that forced a choice, the decision itself, the alternatives
that were considered and passed over, and the consequences — including
the ones that aren't purely positive. They're written after the fact
(this project didn't start with a blank ADR template), reconstructed from
the actual reasoning captured in code comments, `docs/ARCHITECTURE.md`,
`docs/DEPLOYMENT.md`, and the README — but the format going forward is:
before making a comparably significant decision, write the ADR, then
build against it, not the reverse.

| # | Title | Status |
|---|---|---|
| [0001](0001-monolith-with-django-admin.md) | Monolithic Django app, Django Admin as the approval interface | Accepted |
| [0002](0002-database-sqlite-then-postgres.md) | SQLite for intranet/dev, PostgreSQL for cloud or high concurrency | Accepted |
| [0003](0003-single-container-intranet-deployment.md) | Single-container deployment for the intranet; cloud requires added infrastructure | Accepted |
| [0004](0004-custom-user-model-and-admin-scoping.md) | Custom User model; is_staff-based admin scoping instead of per-model permissions | Accepted |
| [0005](0005-formal-exporter-interface.md) | A formal exporter interface (ReportExporter ABC) for Excel/Word/History | Accepted |
| [0006](0006-centralize-business-rules.md) | Every business rule lives in exactly one method, read everywhere else | Accepted |
| [0007](0007-file-retention-policy.md) | Delete originals at approval; scheduled 90-day cleanup otherwise | Accepted |
| [0008](0008-admin-access-model.md) | Admin access model: is_staff-wide Users & Groups, manual provisioning, dual-identifier login | Accepted |
| [0009](0009-rule-based-help-chat.md) | A rule-based help-chat widget, not an LLM integration | Accepted |
| [0010](0010-image-quality-check-not-ocr.md) | A lightweight image-quality check for photo receipts, not OCR | Accepted |
| [0011](0011-jwt-web-authentication.md) | JWT-based authentication for the web portal; Django Admin keeps its own session login | Accepted |
| [0012](0012-shared-frontend-js-not-a-react-rewrite.md) | Incremental shared frontend JS modules instead of a React rewrite | Accepted |

## Format

- **Status**: `Proposed`, `Accepted`, `Superseded by NNNN`, or `Deprecated`.
- **Context**: the problem/constraint that made a decision necessary —
  written so someone who wasn't there can tell *why this was even a
  question*.
- **Decision**: what was actually chosen, in one or two sentences.
- **Alternatives considered**: what else was on the table, and why it
  lost — the part a decision made in isolation (without this record)
  always loses first.
- **Consequences**: what this decision costs, not just what it buys —
  every real decision has both.
