"""Django Admin registrations, split by concern into sibling modules:

- reports.py            ExpenseReportAdmin — the working approval queue
- approved_history.py   ApprovedExpenseReportAdmin — read-only, alphabetical history
- audit_log.py          ExpenseReportAuditLogAdmin — read-only, full audit trail
- forms.py               the admin change form (approve/reject validation)
- inlines.py             TravelDocumentInline, AuditLogInline
- mixins.py              display helpers shared by reports.py and approved_history.py

Each submodule registers its own admin class with `@admin.register(...)` at
import time, so simply importing them here (Django imports this package on
startup via admin.autodiscover()) is what makes them show up in /admin/ —
nothing needs to be re-exported for that to work.
"""
from . import approved_history, audit_log, reports  # noqa: F401
