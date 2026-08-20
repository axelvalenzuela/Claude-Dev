import os

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import FileResponse, Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView

from .excel import build_report_workbook
from .forms import ExpenseReportForm, TravelDocumentForm
from .models import ExpenseReport, ExpenseReportAuditLog, TravelDocument, log_action
from .pdf_analysis import analyze_pdf
from .services import DocumentUploadError, build_travel_document


class OwnedReportMixin:
    """Scopes report lookups to the current user — an employee can only ever
    see/act on their own reports (never another employee's, and never by
    guessing an id)."""

    def get_report(self):
        return get_object_or_404(ExpenseReport, pk=self.kwargs["pk"], user=self.request.user)


class ReportListView(LoginRequiredMixin, ListView):
    model = ExpenseReport
    template_name = "expenses/report_list.html"
    context_object_name = "reports"

    def get_queryset(self):
        return self.request.user.expense_reports.all()


class PreviewDocumentView(LoginRequiredMixin, View):
    """AJAX endpoint used while composing a new report: analyzes one PDF at
    a time (as soon as it's attached, before the report is created or
    anything is saved) and returns the amount/type it detected, so the
    employee can review it live instead of only finding out after saving."""

    def post(self, request):
        file = request.FILES.get("file")
        if not file:
            return JsonResponse({"error": "No file provided."}, status=400)

        if not file.name.lower().endswith(".pdf"):
            return JsonResponse(
                {"is_pdf": False, "extracted_amount": None, "detected_type": None, "detected_type_label": None}
            )

        analysis = analyze_pdf(file)
        detected_type_label = None
        if analysis.detected_type:
            detected_type_label = dict(TravelDocument.DocType.choices).get(analysis.detected_type)

        return JsonResponse(
            {
                "is_pdf": True,
                "extracted_amount": str(analysis.extracted_amount) if analysis.extracted_amount is not None else None,
                "detected_type": analysis.detected_type,
                "detected_type_label": detected_type_label,
            }
        )


class ReportCreateView(LoginRequiredMixin, View):
    """Report creation, with all its receipts attached in the same step.
    Each attached PDF is analyzed live client-side (see PreviewDocumentView)
    so the employee can eyeball the detected amount/type before saving;
    here on the server every file is re-validated and re-analyzed
    independently — the client-side preview is a convenience, not the
    source of truth."""

    template_name = "expenses/report_form.html"

    def get(self, request):
        return render(request, self.template_name, {"form": ExpenseReportForm(), "doc_types": TravelDocument.DocType.choices})

    def post(self, request):
        form = ExpenseReportForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form, "doc_types": TravelDocument.DocType.choices})

        files = request.FILES.getlist("files")
        doc_types = request.POST.getlist("doc_type")
        doc_dates = request.POST.getlist("doc_date")
        doc_amounts = request.POST.getlist("doc_amount")

        documents, errors = [], []
        for index, file in enumerate(files):
            try:
                documents.append(
                    build_travel_document(
                        file,
                        doc_types[index] if index < len(doc_types) else "",
                        doc_dates[index] if index < len(doc_dates) else "",
                        doc_amounts[index] if index < len(doc_amounts) else "",
                    )
                )
            except DocumentUploadError as exc:
                errors.append(f"{file.name}: {exc.message}")

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, self.template_name, {"form": form, "doc_types": TravelDocument.DocType.choices})

        with transaction.atomic():
            report = form.save(commit=False)
            report.user = request.user
            report.save()
            log_action(report, request.user, ExpenseReportAuditLog.Action.CREATED)

            for document in documents:
                document.expense_report = report
                document.save()
                log_action(report, request.user, ExpenseReportAuditLog.Action.DOCUMENT_UPLOADED, document.file_name)

            if request.POST.get("action") == "submit":
                try:
                    report.submit()
                    report.save()
                    log_action(report, request.user, ExpenseReportAuditLog.Action.SUBMITTED)
                    messages.success(request, f"Report created and submitted to {report.supervisor_name} for review.")
                except ValidationError as exc:
                    messages.warning(request, "Saved as a draft instead: " + "; ".join(exc.messages))
            else:
                messages.success(request, "Report saved as a draft.")

        return redirect("reports:detail", pk=report.pk)


class ReportDetailView(LoginRequiredMixin, OwnedReportMixin, DetailView):
    template_name = "expenses/report_detail.html"
    context_object_name = "report"

    def get_object(self, queryset=None):
        return self.get_report()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["upload_form"] = TravelDocumentForm()
        context["daily_totals"] = self.object.daily_totals()
        return context


class UploadDocumentView(LoginRequiredMixin, OwnedReportMixin, View):
    def post(self, request, pk):
        report = self.get_report()

        if report.status != ExpenseReport.Status.DRAFT:
            messages.error(request, "You can only add documents while the report is a draft.")
            return redirect("reports:detail", pk=pk)

        file = request.FILES.get("file")
        if not file:
            messages.error(request, "Select a file.")
            return redirect("reports:detail", pk=pk)

        try:
            document = build_travel_document(
                file, request.POST.get("type"), request.POST.get("document_date"), request.POST.get("amount")
            )
        except DocumentUploadError as exc:
            messages.error(request, f"Couldn't upload the document: {exc.message}")
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
    def post(self, request, pk, doc_id):
        report = self.get_report()

        if report.status != ExpenseReport.Status.DRAFT:
            messages.error(request, "You can only remove documents while the report is a draft.")
            return redirect("reports:detail", pk=pk)

        document = get_object_or_404(TravelDocument, pk=doc_id, expense_report=report)
        file_name = document.file_name
        document.file.delete(save=False)
        document.delete()
        log_action(report, request.user, ExpenseReportAuditLog.Action.DOCUMENT_DELETED, file_name)

        return redirect("reports:detail", pk=pk)


class SubmitReportView(LoginRequiredMixin, OwnedReportMixin, View):
    def post(self, request, pk):
        report = self.get_report()
        try:
            report.submit()
            report.save()
            log_action(report, request.user, ExpenseReportAuditLog.Action.SUBMITTED)
            messages.success(request, f"Report submitted to {report.supervisor_name} for review.")
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        return redirect("reports:detail", pk=pk)


class ExportExcelView(LoginRequiredMixin, OwnedReportMixin, View):
    def get(self, request, pk):
        report = self.get_report()
        return _excel_response(report)


def _excel_response(report):
    workbook = build_report_workbook(report)
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="expense-report-{report.pk}.xlsx"'
    workbook.save(response)
    return response


class DownloadDocumentView(LoginRequiredMixin, OwnedReportMixin, View):
    def get(self, request, pk, doc_id):
        report = self.get_report()
        document = get_object_or_404(TravelDocument, pk=doc_id, expense_report=report)
        if not document.file:
            raise Http404
        return FileResponse(
            document.file.open("rb"), as_attachment=True, filename=os.path.basename(document.file.name)
        )
