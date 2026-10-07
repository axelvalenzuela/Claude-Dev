"""Mixins shared across the employee-facing views in this package."""
from django.shortcuts import get_object_or_404

from ..models import ExpenseReport


class OwnedReportMixin:
    """Scopes report lookups to the current user — an employee can only ever
    see/act on their own reports (never another employee's, and never by
    guessing an id)."""

    def get_report(self):
        return get_object_or_404(ExpenseReport, pk=self.kwargs["pk"], user=self.request.user)
