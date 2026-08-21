"""Company expense-report policy: the numeric limits and cross-cutting
business rules that govern a report, kept separate from models.py so the
ORM schema and the policy that governs it can be read — and changed — on
their own. A policy change here (e.g. raising the daily limit) never
touches the schema; a schema change never has to wade through policy code.

Rules that only concern a single model field (e.g. how big an uploaded
file may be) live in validators.py instead; this module is for rules that
reason about the report as a whole or span multiple documents.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError

# Daily spend over this amount is flagged for review (ExpenseReport.daily_totals()).
DAILY_LIMIT_USD = Decimal("60.00")

# Reports must be submitted within this many days of the trip start (flight date).
SUBMISSION_WINDOW_DAYS = 30

# All the receipts in one report must belong to the same trip: their expense
# dates can't span more than this many days (e.g. a March receipt and a June
# receipt can never be on the same report).
MAX_TRIP_SPAN_DAYS = 21

# All approvals are issued under the CEO's delegated authority.
CEO_NAME = "Steffan Widmer"
CEO_TITLE = "CEO"


def validate_trip_span(dates):
    """Raises if the given expense dates span more than MAX_TRIP_SPAN_DAYS —
    the signal that two unrelated trips are being mixed into one report."""
    dates = [d for d in dates if d is not None]
    if len(dates) < 2:
        return

    span = (max(dates) - min(dates)).days
    if span > MAX_TRIP_SPAN_DAYS:
        raise ValidationError(
            f"These receipts span {span} days ({min(dates):%b %d, %Y} to {max(dates):%b %d, %Y}), "
            f"more than the {MAX_TRIP_SPAN_DAYS}-day limit for a single trip. "
            f"Create a separate report for the other dates."
        )
