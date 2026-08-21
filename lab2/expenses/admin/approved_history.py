"""The approved-reports history: its own section in Django Admin (not just
a filter on the working queue), read-only, sorted alphabetically."""
from django.contrib import admin

from ..models import ApprovedExpenseReport, ExpenseReport
from .inlines import TravelDocumentInline
from .mixins import ExpenseReportDisplayMixin


@admin.register(ApprovedExpenseReport)
class ApprovedExpenseReportAdmin(ExpenseReportDisplayMixin, admin.ModelAdmin):
    """The "approved reports history" the admin can browse — a distinct,
    read-only section of Django Admin (not just a filter on the working
    queue), sorted alphabetically by title for quick lookup rather than by
    date. Approving/rejecting still only happens from ExpenseReportAdmin."""

    ordering = ["title"]
    list_display = ("title", "employee", "employee_number", "department", "total_amount_display", "reviewed_at")
    search_fields = ("title", "user__first_name", "user__email", "user__employee_number")
    readonly_fields = (
        "user",
        "employee_number",
        "title",
        "description",
        "supervisor_name",
        "supervisor_email",
        "status",
        "review_note",
        "approval_clause",
        "submitted_at",
        "reviewed_at",
        "reviewed_by",
        "total_amount_display",
        "exports_display",
    )
    fields = readonly_fields
    inlines = [TravelDocumentInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request).filter(status=ExpenseReport.Status.APPROVED)
        if not request.user.is_superuser and request.user.supervised_department:
            queryset = queryset.filter(user__department=request.user.supervised_department)
        return queryset

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
