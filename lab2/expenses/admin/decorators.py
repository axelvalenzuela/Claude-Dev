"""Decorators for ExpenseReportAdmin's has_*_permission methods (see
reports.py). All three collapse to the exact same check — any active
is_staff account passes; WHICH reports they can see/act on is decided by
get_queryset()'s department scoping, not by Django's per-model Permission
objects — so the check is written once here instead of three times.
"""
from functools import wraps


def staff_permission(method):
    """Wraps a ModelAdmin has_*_permission(self, request, obj=None) method
    so it always returns "is this an active staff account", ignoring the
    wrapped method's own body (kept only for its name/docstring)."""

    @wraps(method)
    def wrapper(self, request, *args, **kwargs):
        return request.user.is_active and request.user.is_staff

    return wrapper
