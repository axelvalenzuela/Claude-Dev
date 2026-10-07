"""Read-only inlines shown on a report's admin change page: its documents
(with the PDF-analysis flags) and its audit trail."""
from django.contrib import admin
from django.utils.html import format_html, format_html_join

from ..models import ExpenseReportAuditLog, TravelDocument


class TravelDocumentInline(admin.TabularInline):
    model = TravelDocument
    extra = 0
    can_delete = False
    fields = (
        "type",
        "document_date",
        "amount_display",
        "file_link",
        "verification_display",
        "uploaded_at",
    )
    readonly_fields = fields

    def amount_display(self, obj):
        if obj.currency == obj.Currency.USD:
            return f"${obj.amount}"
        return format_html('{} {} <span style="color:#777;">(&asymp;${} USD)</span>', obj.amount, obj.currency, obj.amount_usd)

    amount_display.short_description = "Amount"

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

    def verification_display(self, obj):
        # Replaces four raw columns (extracted_amount/amount_mismatch/
        # detected_type/type_mismatch) that meant nothing to a reader who
        # isn't the one who wrote pdf_analysis.py — one human-readable note
        # per mismatch, in the same red used for "over $60/day" elsewhere,
        # or a plain OK when the PDF's own analysis agrees with what the
        # employee entered.
        notes = []
        if obj.amount_mismatch:
            notes.append(
                f"Amount: PDF shows ${obj.extracted_amount}, entered ${obj.amount}"
            )
        if obj.type_mismatch:
            notes.append(
                f"Type: PDF looks like {obj.get_detected_type_display()}, selected {obj.get_type_display()}"
            )
        if not notes:
            return format_html('<span style="color:#2e7d32;">&#10003; OK</span>')
        return format_html(
            '<span style="color:#b02a37;font-weight:bold;">&#9888; {}</span>',
            format_html_join("", "<div>{}</div>", ((note,) for note in notes)),
        )

    verification_display.short_description = "Verification"

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
