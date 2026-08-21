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
            # Opens the raw file directly in a new tab — PDFs/images render
            # natively in the browser, so this is the "preview" of the
            # original receipt while it's still on the server (only until
            # the report is approved — see services.finalize_approval).
            return format_html(
                '{} <a class="button" href="{}" target="_blank">&#128065; Preview</a>',
                obj.file_name, obj.file.url,
            )
        if obj.file_name:
            return format_html(
                '<span title="Original removed after approval">{} (archived — see Excel/Word above)</span>',
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
