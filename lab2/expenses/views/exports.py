"""Downloading a report's Excel/Word. Once a report has been submitted,
these serve the permanent snapshot generated at that time
(services.finalize_submission); a still-draft report has no snapshot yet,
so one is generated on the fly as a preview and not saved anywhere."""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, HttpResponse
from django.views import View

from ..excel import build_report_workbook
from ..word_export import build_report_document
from .mixins import OwnedReportMixin

WORD_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


class ExportExcelView(LoginRequiredMixin, OwnedReportMixin, View):
    def get(self, request, pk):
        report = self.get_report()
        return _excel_response(report)


class ExportWordView(LoginRequiredMixin, OwnedReportMixin, View):
    def get(self, request, pk):
        report = self.get_report()
        return _word_response(report)


def _excel_response(report):
    # Once submitted, the originals are gone and the snapshot generated at
    # that moment is the permanent record — serve that instead of
    # regenerating (which would still work for the numbers, but a fresh
    # Word regeneration couldn't re-embed photos that no longer exist).
    if report.excel_snapshot:
        return FileResponse(
            report.excel_snapshot.open("rb"),
            as_attachment=True,
            filename=f"expense-report-{report.pk}.xlsx",
        )

    workbook = build_report_workbook(report)
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="expense-report-{report.pk}.xlsx"'
    workbook.save(response)
    return response


def _word_response(report):
    if report.word_snapshot:
        return FileResponse(
            report.word_snapshot.open("rb"),
            as_attachment=True,
            filename=f"expense-report-{report.pk}.docx",
        )

    document = build_report_document(report)
    response = HttpResponse(content_type=WORD_CONTENT_TYPE)
    response["Content-Disposition"] = f'attachment; filename="expense-report-{report.pk}.docx"'
    document.save(response)
    return response
