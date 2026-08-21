"""Downloading a report's Excel/Word. Once a report has been approved,
these serve the permanent, RH-named snapshot generated at that time
(services.finalize_approval); a draft or a still-pending-review report has
no snapshot yet, so one is generated on the fly as a preview and not saved
anywhere. Both formats go through the same ReportExporter interface (see
../exporters.py), so this file no longer needs one near-identical function
per format."""
import os

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, HttpResponse
from django.views import View

from ..exporters import ReportExporter, excel_exporter, word_exporter
from ..naming import export_basename
from .mixins import OwnedReportMixin


class ExportExcelView(LoginRequiredMixin, OwnedReportMixin, View):
    def get(self, request, pk):
        return _export_response(self.get_report(), excel_exporter)


class ExportWordView(LoginRequiredMixin, OwnedReportMixin, View):
    def get(self, request, pk):
        return _export_response(self.get_report(), word_exporter)


def _export_response(report, exporter: ReportExporter):
    snapshot = report.excel_snapshot if exporter is excel_exporter else report.word_snapshot

    # Once approved, the originals are gone and the snapshot generated at
    # that moment is the permanent record — serve that instead of
    # regenerating (which would still work for the numbers, but a fresh
    # Word regeneration couldn't re-embed photos that no longer exist).
    if snapshot:
        return FileResponse(snapshot.open("rb"), as_attachment=True, filename=os.path.basename(snapshot.name))

    response = HttpResponse(content_type=exporter.content_type)
    response["Content-Disposition"] = f'attachment; filename="{export_basename(report)}.{exporter.extension}"'
    response.write(exporter.to_bytes(report))
    return response
