"""Decorator for View.post methods that only make sense while a report is
still a draft (adding/removing a document) — both UploadDocumentView and
DeleteDocumentView (see documents.py) had the exact same guard, just with a
different message, before this collapsed it into one place.
"""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from ..models import ExpenseReport


def draft_only(action_description):
    """Wraps a `post(self, request, pk, ...)` method on a view that mixes
    in OwnedReportMixin: redirects back to the report detail page with an
    explanatory message if the report isn't a draft anymore, otherwise
    fetches it once and passes it through to the wrapped method as
    `report=`."""

    def decorator(view_method):
        @wraps(view_method)
        def wrapper(self, request, *args, **kwargs):
            report = self.get_report()
            if report.status != ExpenseReport.Status.DRAFT:
                messages.error(request, f"You can only {action_description} while the report is a draft.")
                return redirect("reports:detail", pk=report.pk)
            return view_method(self, request, *args, report=report, **kwargs)

        return wrapper

    return decorator
