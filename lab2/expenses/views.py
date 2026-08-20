import os

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from django.views.generic import CreateView, DetailView, ListView

from .excel import build_report_workbook
from .forms import ExpenseReportForm, TravelDocumentForm
from .models import ExpenseReport, ExpenseReportAuditLog, TravelDocument, log_action
from .pdf_analysis import analyze_pdf


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


class ReportCreateView(LoginRequiredMixin, CreateView):
    model = ExpenseReport
    form_class = ExpenseReportForm
    template_name = "expenses/report_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        log_action(self.object, self.request.user, ExpenseReportAuditLog.Action.CREATED)
        return response

    def get_success_url(self):
        return reverse("reports:detail", args=[self.object.pk])


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

        form = TravelDocumentForm(request.POST, request.FILES)
        if not form.is_valid():
            errors = "; ".join(f"{field}: {', '.join(errs)}" for field, errs in form.errors.items())
            messages.error(request, f"Couldn't upload the document: {errors}")
            return redirect("reports:detail", pk=pk)

        document = form.save(commit=False)
        document.expense_report = report

        uploaded_file = form.cleaned_data["file"]
        if uploaded_file.name.lower().endswith(".pdf"):
            analysis = analyze_pdf(uploaded_file)
            document.extracted_amount = analysis.extracted_amount
            document.detected_type = analysis.detected_type or ""
            if analysis.extracted_amount is not None:
                document.amount_mismatch = abs(analysis.extracted_amount - document.amount) > 1
            if analysis.detected_type:
                document.type_mismatch = analysis.detected_type != document.type

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
        else:
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
            messages.success(request, "Report submitted for review.")
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
