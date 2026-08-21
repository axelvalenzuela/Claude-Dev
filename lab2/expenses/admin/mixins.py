"""Read-only display helpers shared by ExpenseReportAdmin (the working
approval queue, admin/reports.py) and ApprovedExpenseReportAdmin (the
approved-reports history, admin/approved_history.py) — both render the
same kind of columns/fields, just with different querysets and permissions.
"""
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class ExpenseReportDisplayMixin:
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
            links.append(format_html('<a href="{}" target="_blank">Excel (.xlsx)</a>', obj.excel_snapshot.url))
        if obj.word_snapshot:
            links.append(format_html('<a href="{}" target="_blank">Word (.docx)</a>', obj.word_snapshot.url))
        return mark_safe(" · ".join(links))

    exports_display.short_description = "Archived exports"
