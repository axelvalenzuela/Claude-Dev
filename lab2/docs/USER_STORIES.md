# User stories

What this app does, told from each role's point of view, consolidating
everything built across the project rather than the feature-by-feature
log in the main `README.md`. Each story follows the usual
*As a ⟨role⟩, I want ⟨capability⟩, so that ⟨reason⟩* shape, grouped by
who benefits, with a pointer to where it's implemented for anyone who
wants to trace a story back to code. Stories marked **(done)** are
built and tested today; none in this document are aspirational — the
whole set is a consolidated view of the shipped app, not a backlog.

## Roles

- **Employee** — any registered account (`is_staff=False`). Submits
  their own travel expense reports.
- **Department admin** — `is_staff=True`, `supervised_department` set
  (today: Adrian Heymes, ICS). Reviews and approves/rejects only their
  own department's reports.
- **General admin** — `is_staff=True`, `is_superuser=True` (today: Iris
  Cortez, Karen Plascencia, Steffan Widmer). Reviews and approves/
  rejects every department's reports, and can manage any account.
- **Operator** — whoever deploys and keeps the platform running (not an
  in-app role; no login of their own). Cross-referenced from
  `docs/DEPLOYMENT.md`.

## Employee

- **(done)** As an employee, I want to create my own account with just
  my name, department, and email, so that I don't need an admin to
  provision me one before I can use the platform.
  (`accounts/views.py:SignUpView`, `accounts/forms.py:SignUpForm`)
- **(done)** As an employee, I want to log in with either my email or my
  company employee number, so that I'm not blocked by not remembering
  which one a given form expects.
  (`accounts/backends.py:EmployeeNumberOrEmailBackend`)
- **(done)** As an employee, I want my account locked after 3 wrong
  password attempts in a row, and a working "forgot password" flow to
  unlock it myself, so that a guessed/leaked password alone can't get
  into my account, without needing to call an admin to unlock it.
  (`accounts/security.py`, `accounts/forms.py:LockoutCheckMixin`)
- **(done)** As an employee, I want to start a new expense report and
  attach multiple receipts (PDF or photo) at once, so that I don't have
  to create the report and then add documents one at a time.
  (`expenses/templates/expenses/report_form.html`,
  `expenses/views/reports.py`)
- **(done)** As an employee, I want a PDF receipt's amount and expense
  type detected automatically as soon as I attach it, so that I don't
  have to retype what's already printed on the receipt.
  (`expenses/pdf_analysis.py`, the live-preview endpoint in
  `expenses/views/documents.py`)
- **(done)** As an employee, I want to record which currency each
  receipt was actually paid in (USD or MXN), so that a peso receipt
  isn't silently treated as a dollar amount anywhere in the report.
  (`TravelDocument.currency`, `TravelDocument.amount_usd`)
- **(done)** As an employee, I want to see, before I even submit, which
  days of my trip are flagged against the $60/day policy — and see that
  a flight or hotel day is treated as justified, not as a violation —
  so that I'm not surprised by a rejection over something already
  explainable.
  (`ExpenseReport.daily_totals()`, `report_detail.html`)
- **(done)** As an employee, I want to be blocked from submitting a
  report past its 30-day deadline or spanning more than 21 days, with a
  clear reason why, so that I find out immediately instead of after an
  admin rejects it.
  (`expenses/validators.py`, `expenses/policies.py`)
- **(done)** As an employee, I want to remove a single attached file
  before I submit — by drag-and-drop or by a per-file remove button — so
  that a mis-picked receipt doesn't force me to re-select the whole
  batch.
  (`expenses/templates/expenses/report_form.html`)
- **(done)** As an employee, I want to see my report's status (draft,
  submitted, approved, rejected) and, once reviewed, the reviewer's note
  — including on the reports list itself, not just after opening one —
  so that I know what happened and why without hunting for it.
  (`report_list.html`, `report_history.html`,
  `_status_badge.html`)
- **(done)** As an employee, I want a banner on my next page load telling
  me my report was approved or rejected, with the note right there, so
  that I don't have to go looking for the outcome myself.
  (`accounts/context_processors.py:recent_review_notification`)
- **(done)** As an employee, once my report is approved, I want to
  download the final Excel and Word versions, so that I have the
  permanent record even after the originals I uploaded are gone.
  (`expenses/views/exports.py`, `expenses/exporters.py`)
- **(done)** As an employee, I want my original receipt files to stay
  available while my report is still pending review, so that I (or the
  reviewing admin) can still look at them before a decision is made.
  (`expenses/services.py:finalize_approval` — deletion only on approval,
  see `docs/adr/0007-file-retention-policy.md`)

## Department admin (e.g. Adrian Heymes, ICS)

- **(done)** As a department admin, I want to see only my own
  department's submitted reports — never another department's, even by
  guessing a report's URL directly — so that I only ever review what's
  actually mine to review.
  (`ExpenseReportAdmin.get_queryset`,
  `accounts/tests/test_department_scoping.py`)
- **(done)** As a department admin, I want a Dashboard that shows what's
  waiting on me right now (KPI tiles, a Pending/Approved filterable
  table), scoped to my department, so that I don't have to dig through a
  full report list to find what needs my attention.
  (`accounts/context_processors.py:pending_reports_notification`,
  `approved_reports_table`; `templates/admin/index.html`)
- **(done)** As a department admin, I want to approve a report only
  after explicitly acknowledging the CEO's delegated approval authority,
  and to be required to leave a note when I reject one, so that every
  decision carries an explicit, auditable justification.
  (`ExpenseReport.approve()`/`reject()`, `expenses/policies.py:CEO_NAME`)
- **(done)** As a department admin, I want to preview or download a
  report's Excel/Word before it's approved, so that I can check the
  final format without having to approve it first to see it.
  (`ExpenseReportAdmin.preview_excel`/`preview_word`)
- **(done)** As a department admin, I want a downloadable history of a
  report — every status change, who made it, and any note (rejection
  notes included) — so that a multi-round review has a clear paper
  trail I can hand off or reference later.
  (`expenses/history_export.py`, the "Download history" object-tool)
- **(done)** As a department admin, I want to search for any employee
  registered on the platform, not just ones who've submitted something,
  so that I can look someone up before they've done anything.
  (`accounts/context_processors.py:employee_directory`)
- **(done)** As a department admin, I want to view and manage Users &
  Groups myself — including granting someone else admin access — so
  that I'm not dependent on a general admin for something I can safely
  do myself.
  (`accounts/admin.py:StaffManagedAdminMixin`,
  `docs/adr/0008-admin-access-model.md`)
- **(done)** As a department admin, I want a Policies tab and a Help/FAQ
  tab describing every rule the platform enforces and exactly where to
  click for common situations, so that I have a self-service reference
  instead of having to ask someone or read the source code.
  (`templates/admin/index.html`'s Policies/Help panels)

## General admin (Iris Cortez, Karen Plascencia, Steffan Widmer)

- **(done)** As a general admin, I want to see and approve every
  department's reports, not just one, so that reports don't stall when a
  department admin is unavailable and so there's always a catch-all
  approver.
  (`is_superuser=True`, unscoped in `ExpenseReportAdmin.get_queryset`)
- **(done)** As a general admin, I want an approval-rate donut chart and
  KPI tiles summarizing what I've reviewed, so that I have a quick sense
  of throughput without counting rows myself.
  (`accounts/context_processors.py:approval_chart`)
- **(done)** As a general admin, I want everything a department admin
  has (Dashboard, Users & Groups, history downloads, Policies/Help),
  unscoped, so that I never lose visibility a department admin has.
  (Same views/context processors as above, minus the department filter)
- **(done)** As a general admin, I want a badge showing whether I'm
  signed in as the general admin or a department admin, visible on every
  admin page, so that the difference between the two roles isn't only
  observable indirectly from which reports happen to show up.
  (`accounts/context_processors.py:admin_scope_badge`)

## Cross-cutting / platform

- **(done)** As anyone with a login, I want every login attempt —
  successful or not, against a real account or not — recorded with who,
  when, and from where, so that suspicious activity is traceable after
  the fact.
  (`accounts/signals.py`, `accounts.models.LoginEvent`)
- **(done)** As anyone with a login, I want the account-lockout counter
  to be the same account no matter whether I typed my email or my
  employee number on a given failed attempt, so that the protection
  can't be bypassed by alternating identifiers.
  (`accounts/models.py:find_user_by_login_identifier`)
- **(done)** As the company, I want uploaded receipt files that are
  never approved (still pending, or rejected — there's no resubmit flow)
  to eventually be cleaned up automatically, so that storage doesn't
  grow unbounded from abandoned reports.
  (`expenses/management/commands/cleanup_old_documents.py`,
  `docs/adr/0007-file-retention-policy.md`)
- **(done)** As the company, I want the admin roster limited to four
  named people by policy, with no self-service way to become an admin,
  so that admin access stays a deliberate, personal decision rather than
  something anyone can grant themselves.
  (Documented on the Policies/Help tabs; enforced by process, see
  `docs/adr/0008-admin-access-model.md`'s consequences)

## Operator (deployment / infrastructure — no in-app login)

- **(done)** As the operator, I want a single Docker image that runs the
  whole app (`gunicorn` + WhiteNoise, no separate static-file server), so
  that standing up the intranet deployment is `docker compose up
  --build` and nothing else.
  (`Dockerfile`, `docker-compose.yml`,
  `docs/adr/0003-single-container-intranet-deployment.md`)
- **(done)** As the operator, I want the database to be a single file by
  default (SQLite), with a documented, code-free path to point at a real
  Postgres server instead, so that the intranet deployment stays simple
  while a growth path exists without a rewrite.
  (`config/settings.py`'s `DATABASES`,
  `docs/adr/0002-database-sqlite-then-postgres.md`)
- **(done)** As the operator, I want a documented list of what changes
  before deploying to a cloud provider (Azure/AWS/GCP) — managed
  Postgres becomes mandatory, `media/` needs object storage, secrets
  move out of `.env` — so that I don't discover a data-loss risk (SQLite
  or local disk on ephemeral cloud storage) only after it happens.
  (`docs/DEPLOYMENT.md`'s "Desplegar en un proveedor de nube" section)
- **(done)** As the operator, I want a CI pipeline that runs the test
  suite, `manage.py check --deploy`, and a Docker build on every push,
  so that a configuration regression or a broken image is caught before
  it reaches the server.
  (`.github/workflows/lab2-ci.yml`)
- **(done)** As the operator, I want the 90-day file-retention cleanup to
  be a plain management command I schedule myself (cron / Task Scheduler
  / a container sidecar), not something that runs invisibly inside
  request handling, so that I control when it runs and can dry-run it
  first.
  (`expenses/management/commands/cleanup_old_documents.py --dry-run`)
