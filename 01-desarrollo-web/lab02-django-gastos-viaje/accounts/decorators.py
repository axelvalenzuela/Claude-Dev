"""Shared ModelAdmin permission decorator. Lives here (not in a specific
app's admin/ package) because both accounts (UserAdmin, GroupAdmin) and
expenses (ExpenseReportAdmin) use it, and accounts is the lower-level app
neither depends on the other to import from."""
from functools import wraps


def staff_permission(method):
    """Wraps a ModelAdmin has_*_permission(self, request, obj=None) method
    so it always returns "is this an active staff account", ignoring the
    wrapped method's own body (kept only for its name/docstring). Every
    admin-facing model in this app treats is_staff as the whole boundary —
    WHICH rows a given admin can see/act on is decided by each
    ModelAdmin's own get_queryset() scoping, not by Django's per-model
    Permission objects, so the check only needs writing once, here."""

    @wraps(method)
    def wrapper(self, request, *args, **kwargs):
        return request.user.is_active and request.user.is_staff

    return wrapper
