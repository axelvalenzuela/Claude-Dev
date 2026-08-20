"""Shared logic for turning an uploaded file + form fields into a
TravelDocument, used both by the single-document upload on the report detail
page and by the multi-file attachment step on report creation."""
from .forms import TravelDocumentForm
from .pdf_analysis import analyze_pdf


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
