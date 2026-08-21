"""Views for the report itself: the working list, the alphabetical
history, creating one (with its receipts attached in the same step),
viewing its detail, and submitting it for review.

Document-level actions (upload/delete/download/preview) live in
documents.py; downloading the generated Excel/Word live in exports.py —
split out because they're a different concern (a single file response)
from the report-shaped views here, even though they hang off the same URLs.
"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import redirect, render
from django.views import View
from django.views.generic import DetailView, ListView

from ..forms import ExpenseReportForm, TravelDocumentForm
from ..models import ExpenseReport, ExpenseReportAuditLog, TravelDocument, log_action
from ..policies import validate_trip_span
from ..services import DocumentUploadError, build_travel_document, finalize_submission
from .mixins import OwnedReportMixin


class ReportListView(LoginRequiredMixin, ListView):
    """The employee's working list: every report regardless of status
    (draft/submitted/approved/rejected), most recently created first — this
    is where they go to keep building a draft or check on something they
    just sent."""

    model = ExpenseReport
    template_name = "expenses/report_list.html"
    context_object_name = "reports"

    def get_queryset(self):
        return self.request.user.expense_reports.all()


class ReportHistoryView(LoginRequiredMixin, ListView):
    """A separate, alphabetically-sorted archive of everything the employee
    has ever sent (submitted, approved, or rejected — never drafts, which
    haven't been sent to anyone yet). Meant for looking something up by
    name later, not for tracking what's currently in progress — that's
    what ReportListView is for."""

    template_name = "expenses/report_history.html"
    context_object_name = "reports"

    def get_queryset(self):
        return (
            self.request.user.expense_reports.exclude(status=ExpenseReport.Status.DRAFT)
            .order_by("title")
        )


class ReportCreateView(LoginRequiredMixin, View):
    """Report creation, with all its receipts attached in the same step.
    Each attached PDF is analyzed live client-side (see
    documents.PreviewDocumentView) so the employee can eyeball the detected
    amount/type before saving; here on the server every file is
    re-validated and re-analyzed independently — the client-side preview is
    a convenience, not the source of truth."""

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

        if not errors and documents:
            try:
                validate_trip_span([document.document_date for document in documents])
            except ValidationError as exc:
                errors.append("; ".join(exc.messages))

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
                    finalize_submission(report, request.user)
                    messages.success(
                        request,
                        f"Report created and submitted to {report.supervisor_name} for review. "
                        f"The original files were archived into the Excel/Word exports below.",
                    )
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


class SubmitReportView(LoginRequiredMixin, OwnedReportMixin, View):
    def post(self, request, pk):
        report = self.get_report()
        try:
            with transaction.atomic():
                report.submit()
                report.save()
                log_action(report, request.user, ExpenseReportAuditLog.Action.SUBMITTED)
                finalize_submission(report, request.user)
            messages.success(
                request,
                f"Report submitted to {report.supervisor_name} for review. "
                f"The original files were archived into the Excel/Word exports below.",
            )
        except ValidationError as exc:
            messages.error(request, "; ".join(exc.messages))
        return redirect("reports:detail", pk=pk)
