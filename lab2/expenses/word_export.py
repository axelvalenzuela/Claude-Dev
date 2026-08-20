"""Builds the .docx (editable Word) expense report from an ExpenseReport.

This is the second permanent record generated at submission time, alongside
the .xlsx from expenses/excel.py — see expenses/services.py:finalize_submission.
It captures the same structured data as the Excel export, plus an embedded
thumbnail of every photo receipt (JPG/PNG). PDF receipts are listed by name
only (rendering a PDF page to an image would need a system-level dependency
like poppler, which isn't worth adding just for a thumbnail).

This function MUST run before the original TravelDocument.file is deleted —
once that happens there's nothing left to embed a thumbnail from.
"""
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt

from .models import DAILY_LIMIT_USD

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")


def build_report_document(report) -> Document:
    document = Document()

    document.add_heading("Travel expense report", level=1)

    trip_range = report.trip_date_range
    trip_range_text = f"{trip_range[0]:%Y-%m-%d} to {trip_range[1]:%Y-%m-%d}" if trip_range else "—"

    info_table = document.add_table(rows=0, cols=2)
    info_table.style = "Light Grid Accent 1"
    for label, value in [
        ("Employee", report.user.get_full_name() or report.user.email),
        ("Employee #", report.user.employee_number or "—"),
        ("Department", report.user.department),
        ("Supervisor", f"{report.supervisor_name} ({report.supervisor_email})" if report.supervisor_email else report.supervisor_name),
        ("Title", report.title),
        ("Trip dates", trip_range_text),
        ("Status", report.get_status_display()),
        ("Created", report.created_at.strftime("%Y-%m-%d %H:%M")),
    ]:
        row = info_table.add_row().cells
        row[0].text, row[1].text = label, value

    if report.reviewed_at:
        for label, value in [
            ("Reviewed", report.reviewed_at.strftime("%Y-%m-%d %H:%M")),
            ("Review note", report.review_note or "—"),
        ]:
            row = info_table.add_row().cells
            row[0].text, row[1].text = label, value
        if report.approval_clause:
            row = info_table.add_row().cells
            row[0].text, row[1].text = "Approval clause", report.approval_clause

    document.add_heading("Expenses", level=2)
    expense_table = document.add_table(rows=1, cols=5)
    expense_table.style = "Light Grid Accent 1"
    header_cells = expense_table.rows[0].cells
    for cell, text in zip(header_cells, ["#", "Type", "Date", "File", "Amount"]):
        cell.text = text
        cell.paragraphs[0].runs[0].bold = True

    total = 0
    # Alphabetically by expense type, then chronologically within each type.
    for index, doc in enumerate(report.documents.order_by("type", "document_date"), start=1):
        row = expense_table.add_row().cells
        row[0].text = str(index)
        row[1].text = doc.get_type_display()
        row[2].text = doc.document_date.strftime("%Y-%m-%d")
        row[3].text = doc.file_name
        row[4].text = f"${doc.amount:.2f}"
        total += doc.amount

    total_paragraph = document.add_paragraph()
    total_run = total_paragraph.add_run(f"Total: ${total:.2f}")
    total_run.bold = True
    total_run.font.size = Pt(12)

    _add_receipt_captures(document, report)
    _add_daily_breakdown(document, report)

    return document


def _add_receipt_captures(document: Document, report) -> None:
    """Embeds a thumbnail of every photo receipt still on disk. Called
    before the originals are deleted — this is the permanent visual record
    of what the JPG/PNG receipts looked like."""
    photo_docs = [
        doc
        for doc in report.documents.order_by("type", "document_date")
        if doc.file and doc.file_name.lower().endswith(IMAGE_EXTENSIONS)
    ]
    if not photo_docs:
        return

    document.add_heading("Receipt captures", level=2)
    for doc in photo_docs:
        caption = document.add_paragraph()
        caption.add_run(f"{doc.get_type_display()} — {doc.document_date:%Y-%m-%d} — ${doc.amount:.2f}").bold = True
        try:
            doc.file.open("rb")
            document.add_picture(doc.file, width=Inches(3))
            document.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.LEFT
        except Exception:  # noqa: BLE001 - a bad/unreadable image must never block the export
            document.add_paragraph("(Could not embed this image.)")
        finally:
            doc.file.close()


def _add_daily_breakdown(document: Document, report) -> None:
    document.add_heading(f"Daily spend vs. ${DAILY_LIMIT_USD}/day policy", level=2)
    table = document.add_table(rows=1, cols=3)
    table.style = "Light Grid Accent 1"
    for cell, text in zip(table.rows[0].cells, ["Date", "Daily total", "Over policy limit?"]):
        cell.text = text
        cell.paragraphs[0].runs[0].bold = True

    for day in report.daily_totals():
        row = table.add_row().cells
        row[0].text = day["date"].strftime("%Y-%m-%d")
        row[1].text = f"${day['total']:.2f}"
        row[2].text = "Yes" if day["over_limit"] else "No"
