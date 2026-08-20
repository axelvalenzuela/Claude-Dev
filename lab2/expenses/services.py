"""Shared logic for turning an uploaded file + form fields into a
TravelDocument, used both by the single-document upload on the report detail
page and by the multi-file attachment step on report creation."""
from io import BytesIO

from django.core.files.base import ContentFile

from .excel import build_report_workbook
from .forms import TravelDocumentForm
from .models import ExpenseReportAuditLog, log_action
from .pdf_analysis import analyze_pdf
from .word_export import build_report_document


class DocumentUploadError(Exception):
    """Raised when a file's accompanying type/date/amount fail validation."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def build_travel_document(file, doc_type, document_date, amount):
    """Validate and build an unsaved TravelDocument for `file`, running the
    best-effort PDF analysis. Caller is responsible for setting
    `expense_report` and calling `.save()`."""
    form = TravelDocumentForm(
        data={"type": doc_type, "document_date": document_date, "amount": amount},
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


def finalize_submission(report, actor) -> None:
    """Runs right after a report successfully moves from draft to submitted.

    Company policy: the original receipt uploads (PDFs/photos) aren't kept
    forever — storing every employee's raw receipts indefinitely isn't
    sustainable. Instead, an Excel workbook and a Word document are
    generated *first*, capturing every expense's data (and, for photo
    receipts, an embedded thumbnail) permanently on the report. Only once
    both are safely saved are the original files deleted from disk — the
    two generated documents become the report's lasting record from this
    point on. TravelDocument rows themselves (type/amount/date/flags) are
    kept, so the $60/day breakdown, admin review, and history views keep
    working exactly as before; only the underlying files are gone.

    Callers are expected to run this inside the same transaction as the
    submit() call, so if anything here fails, the whole submission rolls
    back rather than leaving the report submitted with no exports and no
    originals.
    """
    excel_bytes = BytesIO()
    build_report_workbook(report).save(excel_bytes)
    excel_bytes.seek(0)

    word_bytes = BytesIO()
    build_report_document(report).save(word_bytes)
    word_bytes.seek(0)

    # Both exports must exist before anything gets deleted.
    report.excel_snapshot.save(f"report-{report.pk}.xlsx", ContentFile(excel_bytes.read()), save=False)
    report.word_snapshot.save(f"report-{report.pk}.docx", ContentFile(word_bytes.read()), save=False)
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
        "Original receipt files removed after submission; Excel/Word exports generated.",
    )
