"""Shared logic for turning an uploaded file + form fields into a
TravelDocument, used both by the single-document upload on the report detail
page and by the multi-file attachment step on report creation."""
from django.core.files.base import ContentFile

from .exporters import excel_exporter, word_exporter
from .forms import TravelDocumentForm
from .models import ExpenseReportAuditLog, log_action
from .naming import export_basename
from .pdf_analysis import analyze_pdf


class DocumentUploadError(Exception):
    """Raised when a file's accompanying type/date/amount fail validation."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def build_travel_document(file, doc_type, document_date, amount, currency="USD", vendor_name="", backup_type="invoice"):
    """Validate and build an unsaved TravelDocument for `file`, running the
    best-effort PDF analysis. Caller is responsible for setting
    `expense_report` and calling `.save()`. `currency`/`vendor_name`/
    `backup_type` default to values matching TravelDocument's own model
    defaults, for callers that don't ask the employee to choose."""
    form = TravelDocumentForm(
        data={
            "type": doc_type,
            "document_date": document_date,
            "amount": amount,
            "currency": currency,
            "vendor_name": vendor_name,
            "backup_type": backup_type,
        },
        files={"file": file},
    )
    if not form.is_valid():
        errors = "; ".join(f"{field}: {', '.join(errs)}" for field, errs in form.errors.items())
        raise DocumentUploadError(errors)

    document = form.save(commit=False)

    if file.name.lower().endswith(".pdf"):
        analysis = analyze_pdf(file)
        document.extracted_amount = analysis.extracted_amount
        document.detected_type = analysis.detected_type or ""
        if analysis.extracted_amount is not None:
            document.amount_mismatch = abs(analysis.extracted_amount - document.amount) > 1
        if analysis.detected_type:
            document.type_mismatch = analysis.detected_type != document.type

    return document


def finalize_approval(report, actor) -> None:
    """Runs right after a report is approved (see
    ExpenseReportAdmin.save_model in expenses/admin/reports.py).

    Company policy: the original receipt uploads (PDFs/photos) stay
    available for as long as a report is only submitted/pending review —
    an employee or admin may still need to check them while the report is
    being decided on. Once approved, though, they aren't kept forever:
    storing every employee's raw receipts indefinitely isn't sustainable.
    Instead, an Excel workbook and a Word document are generated *first*
    (now reflecting the reviewer, the review note, and the CEO approval
    clause, since the report is already approved at this point), named per
    RH's convention — employee name, submission date, employee number, an
    "APROBADO" marker (see expenses/naming.py) — capturing every expense's
    data and, for photo receipts, an embedded thumbnail. Only once both are
    safely saved are the original files deleted from disk — the two
    generated documents become the report's lasting record from this point
    on. TravelDocument rows themselves (type/amount/date/flags) are kept,
    so the $60/day breakdown, admin review, and history views keep working
    exactly as before; only the underlying files are gone.

    A rejected report is untouched by any of this — there's no resubmission
    flow, so its original files stay available indefinitely alongside the
    rejection reason.

    Callers are expected to run this inside the same transaction as the
    approve() call (Django admin's changeform view already wraps save_model
    in one), so if anything here fails, the whole approval rolls back
    rather than leaving the report approved with no exports.
    """
    basename = export_basename(report, approved=True)

    # Both exports must exist before anything gets deleted.
    report.excel_snapshot.save(f"{basename}.{excel_exporter.extension}", ContentFile(excel_exporter.to_bytes(report)), save=False)
    report.word_snapshot.save(f"{basename}.{word_exporter.extension}", ContentFile(word_exporter.to_bytes(report)), save=False)
    report.save(update_fields=["excel_snapshot", "word_snapshot"])

    for document in report.documents.all():
        if document.file:
            document.file.delete(save=False)
            document.file = None
            document.save(update_fields=["file"])

    log_action(
        report,
        actor,
        ExpenseReportAuditLog.Action.DOCUMENT_DELETED,
        "Original receipt files removed after approval; Excel/Word exports generated and named per RH convention.",
    )
