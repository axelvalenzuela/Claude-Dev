"""Formal interface for a report export format (an enterprise-style
"Separated Interface": excel.py/word_export.py keep owning *what content*
goes in the file; this module is the only place that knows there are two
export formats and how each is served/named).

Before this, `finalize_approval` (services.py) and the download views
(views/exports.py) each repeated their own "build the document, render it
to bytes, then save/serve it" ceremony once per format — four near-
identical blocks across two files, and the content types were hardcoded a
second time in views/exports.py. Both call sites now go through the two
exporter instances below instead.
"""
from abc import ABC, abstractmethod
from io import BytesIO


class ReportExporter(ABC):
    """One export format. `build()` returns an object with a `.save(stream)`
    method — openpyxl's Workbook and python-docx's Document both already
    satisfy that, so no adapter is needed for either."""

    extension: str
    content_type: str

    @abstractmethod
    def build(self, report):
        """Builds the format-specific document for `report`."""

    def to_bytes(self, report) -> bytes:
        buffer = BytesIO()
        self.build(report).save(buffer)
        return buffer.getvalue()


class ExcelExporter(ReportExporter):
    extension = "xlsx"
    content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def build(self, report):
        from .excel import build_report_workbook

        return build_report_workbook(report)


class WordExporter(ReportExporter):
    extension = "docx"
    content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def build(self, report):
        from .word_export import build_report_document

        return build_report_document(report)


class HistoryExporter(ReportExporter):
    """Not one of the two permanent export formats — this always builds
    live from the audit log (expenses/history_export.py), never from a
    saved snapshot, since it needs to reflect the trail as it stands right
    now rather than a point-in-time copy."""

    extension = "docx"
    content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    def build(self, report):
        from .history_export import build_history_document

        return build_history_document(report)


excel_exporter = ExcelExporter()
word_exporter = WordExporter()
history_exporter = HistoryExporter()
