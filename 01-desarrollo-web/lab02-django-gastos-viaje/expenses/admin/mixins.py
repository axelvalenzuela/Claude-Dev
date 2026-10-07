"""Read-only display helpers shared by ExpenseReportAdmin (the working
approval queue, admin/reports.py) and ApprovedExpenseReportAdmin (the
approved-reports history, admin/approved_history.py) — both render the
same kind of columns/fields, just with different querysets and permissions.
"""
from django.utils.html import format_html
from django.utils.safestring import mark_safe


STATUS_BADGES = {
    "draft": ("#6c757d", "Draft"),
    "submitted": ("#e2960f", "⏳ Pending review"),
    "approved": ("#2e7d32", "✅ Approved"),
    "rejected": ("#c62828", "⛔ Rejected"),
}


class ExpenseReportDisplayMixin:
    def status_badge(self, obj):
        # A colored, iconed pill instead of Django's default plain-text
        # status column — approved vs. not-approved should be readable at
        # a glance in a changelist full of rows, not only after reading
        # each title/status word individually. The status-pill-{status}
        # class (not just the inline color) is what lets the "still
        # needs a decision" pulse animation (brand.css) target the
        # submitted state specifically, without pulsing an already-
        # resolved approved/rejected pill too.
        color, label = STATUS_BADGES.get(obj.status, ("#6c757d", obj.get_status_display()))
        return format_html(
            '<span class="status-pill status-pill-{}" style="background-color:{};">{}</span>',
            obj.status, color, label,
        )

    status_badge.short_description = "Status"
    status_badge.admin_order_field = "status"

    def employee(self, obj):
        return obj.user.get_full_name() or obj.user.email

    employee.short_description = "Employee"

    def employee_number(self, obj):
        return obj.user.employee_number or "—"

    employee_number.short_description = "Employee #"

    def department(self, obj):
        return obj.user.department

    def total_amount_display(self, obj):
        return f"${obj.total_amount:,.2f}"

    total_amount_display.short_description = "Total"

    def exports_display(self, obj):
        if not obj.excel_snapshot and not obj.word_snapshot:
            return "Not generated yet (only saved once the report is approved)."
        links = []
        if obj.excel_snapshot:
            links.append(
                format_html('<a class="button" href="{}" target="_blank">&#128202; Excel (.xlsx)</a>', obj.excel_snapshot.url)
            )
        if obj.word_snapshot:
            links.append(
                format_html('<a class="button" href="{}" target="_blank">&#128196; Word (.docx)</a>', obj.word_snapshot.url)
            )
        return mark_safe(" &nbsp; ".join(links))

    exports_display.short_description = "Archived exports"
