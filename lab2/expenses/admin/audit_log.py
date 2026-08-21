"""The full, read-only audit trail across every report — the admin's
traceability view of who did what, and when."""
from django.contrib import admin

from ..models import ExpenseReportAuditLog


@admin.register(ExpenseReportAuditLog)
class ExpenseReportAuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "report", "actor", "action", "note")
    list_filter = ("action",)
    search_fields = ("report__title", "actor__email", "note")
    readonly_fields = ("report", "actor", "action", "note", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
