"""Read-only inlines shown on a report's admin change page: its documents
(with the PDF-analysis flags) and its audit trail."""
from django.contrib import admin
from django.utils.html import format_html

from ..models import ExpenseReportAuditLog, TravelDocument


class TravelDocumentInline(admin.TabularInline):
    model = TravelDocument
    extra = 0
    can_delete = False
    fields = (
        "type",
        "document_date",
        "amount",
        "file_link",
        "extracted_amount",
        "amount_mismatch",
        "detected_type",
        "type_mismatch",
        "uploaded_at",
    )
    readonly_fields = fields

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.file.url, obj.file_name)
        if obj.file_name:
            return format_html(
                '<span title="Original removed after submission">{} (archived — see Excel/Word)</span>',
                obj.file_name,
            )
        return "—"

    file_link.short_description = "File"

    def has_add_permission(self, request, obj=None):
        return False


class AuditLogInline(admin.TabularInline):
    model = ExpenseReportAuditLog
    extra = 0
    can_delete = False
    fields = ("created_at", "actor", "action", "note")
    readonly_fields = fields
    ordering = ["-created_at"]

    def has_add_permission(self, request, obj=None):
        return False
