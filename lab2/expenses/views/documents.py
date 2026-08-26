"""Views for individual documents on a report: adding one, removing one,
downloading the original (while it still exists — see
services.finalize_approval for why it might not, once the report is
approved), and the live AJAX preview used while composing a report."""
import os

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from ..image_analysis import analyze_image
from ..models import TravelDocument, ExpenseReportAuditLog, log_action
from ..pdf_analysis import analyze_pdf
from ..policies import validate_trip_span
from ..services import DocumentUploadError, build_travel_document
from .decorators import draft_only
from .mixins import OwnedReportMixin


EMPTY_ANALYSIS = {
    "is_pdf": False,
    "is_image": False,
    "extracted_amount": None,
    "detected_type": None,
    "detected_type_label": None,
    "extracted_date": None,
    "extracted_vendor": None,
    "detected_currency": None,
    "image_is_readable": None,
    "image_is_blurry": None,
    "image_width": None,
    "image_height": None,
}

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")


class PreviewDocumentView(LoginRequiredMixin, View):
    """AJAX endpoint used while composing a new report: analyzes one file
    at a time (as soon as it's attached, before the report is created or
    anything is saved). For a PDF, that's the amount/type/date/vendor/
    currency it can read off the text layer (pdf_analysis.analyze_pdf) —
    the report gets pre-filled from the receipt instead of the employee
    retyping what's already printed on it. For a photo, there's no text
    to read (this never does OCR — see expenses/image_analysis.py's
    docstring for why), but it still checks whether the photo itself is
    even legible (readable, sharp, a real size) so a blurry or corrupt
    upload gets flagged immediately instead of only being noticed later."""

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return JsonResponse({"error": "No file provided."}, status=400)

        name = file.name.lower()
        if name.endswith(".pdf"):
            return JsonResponse(self._pdf_response(file))
        if name.endswith(IMAGE_EXTENSIONS):
            return JsonResponse(self._image_response(file))
        return JsonResponse(EMPTY_ANALYSIS)

    def _pdf_response(self, file):
        analysis = analyze_pdf(file)
        detected_type_label = None
        if analysis.detected_type:
            detected_type_label = dict(TravelDocument.DocType.choices).get(analysis.detected_type)

        return {
            **EMPTY_ANALYSIS,
            "is_pdf": True,
            "extracted_amount": str(analysis.extracted_amount) if analysis.extracted_amount is not None else None,
            "detected_type": analysis.detected_type,
            "detected_type_label": detected_type_label,
            "extracted_date": analysis.extracted_date.isoformat() if analysis.extracted_date else None,
            "extracted_vendor": analysis.extracted_vendor,
            "detected_currency": analysis.detected_currency,
        }

    def _image_response(self, file):
        analysis = analyze_image(file)
        return {
            **EMPTY_ANALYSIS,
            "is_image": True,
            "image_is_readable": analysis.is_readable,
            "image_is_blurry": analysis.is_blurry,
            "image_width": analysis.width,
            "image_height": analysis.height,
        }


class UploadDocumentView(LoginRequiredMixin, OwnedReportMixin, View):
    @draft_only("add documents")
    def post(self, request, pk, report):
        file = request.FILES.get("file")
        if not file:
            messages.error(request, "Select a file.")
            return redirect("reports:detail", pk=pk)

        try:
            document = build_travel_document(
                file,
                request.POST.get("type"),
                request.POST.get("document_date"),
                request.POST.get("amount"),
                currency=request.POST.get("currency", "USD"),
                vendor_name=request.POST.get("vendor_name", ""),
                backup_type=request.POST.get("backup_type", "invoice"),
            )
        except DocumentUploadError as exc:
            messages.error(request, f"Couldn't upload the document: {exc.message}")
            return redirect("reports:detail", pk=pk)

        try:
            existing_dates = [d.document_date for d in report.documents.all()]
            validate_trip_span(existing_dates + [document.document_date])
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
            return redirect("reports:detail", pk=pk)

        document.expense_report = report
        document.save()
        log_action(report, request.user, ExpenseReportAuditLog.Action.DOCUMENT_UPLOADED, document.file_name)

        if document.amount_mismatch:
            messages.warning(
                request,
                f"Heads up: the PDF seems to show ${document.extracted_amount}, "
                f"but you entered ${document.amount}. Please double check.",
            )
        if document.type_mismatch:
            messages.warning(
                request,
                f"Heads up: the PDF looks like a {document.get_detected_type_display()} receipt, "
                f"but you selected {document.get_type_display()}.",
            )
        if not document.amount_mismatch and not document.type_mismatch:
            messages.success(request, "Document added.")

        return redirect("reports:detail", pk=pk)


class DeleteDocumentView(LoginRequiredMixin, OwnedReportMixin, View):
    @draft_only("remove documents")
    def post(self, request, pk, doc_id, report):
        document = get_object_or_404(TravelDocument, pk=doc_id, expense_report=report)
        file_name = document.file_name
        document.file.delete(save=False)
        document.delete()
        log_action(report, request.user, ExpenseReportAuditLog.Action.DOCUMENT_DELETED, file_name)

        return redirect("reports:detail", pk=pk)


class DownloadDocumentView(LoginRequiredMixin, OwnedReportMixin, View):
    def get(self, request, pk, doc_id):
        report = self.get_report()
        document = get_object_or_404(TravelDocument, pk=doc_id, expense_report=report)
        if not document.file:
            # Expected once the report has been approved — the original
            # was archived into the Excel/Word exports and removed.
            raise Http404
        return FileResponse(
            document.file.open("rb"), as_attachment=True, filename=os.path.basename(document.file.name)
        )
