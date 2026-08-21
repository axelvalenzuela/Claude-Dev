"""Builds the .xlsx expense report from an ExpenseReport, including the
per-day breakdown against the company's $60/day policy and, once approved,
the CEO approval clause."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from .policies import DAILY_LIMIT_USD

HEADER_FILL = PatternFill("solid", fgColor="D9D9D9")
VIOLATION_FILL = PatternFill("solid", fgColor="F8D7DA")
# A flight or hotel charge routinely clears $60/day on its own — that's
# expected, not a policy question, so it gets a neutral informational
# color instead of the red used for an unexplained overage.
JUSTIFIED_FILL = PatternFill("solid", fgColor="D9E8F5")


def build_report_workbook(report) -> Workbook:
    wb = Workbook()
    sheet = wb.active
    sheet.title = "Expense report"

    sheet["A1"] = "Travel expense report"
    sheet["A1"].font = Font(bold=True, size=14)

    trip_range = report.trip_date_range
    trip_range_text = f"{trip_range[0]:%Y-%m-%d} to {trip_range[1]:%Y-%m-%d}" if trip_range else "—"

    info_rows = 2
    for label, value in [
        ("Employee", report.user.get_full_name() or report.user.email),
        ("Employee #", report.user.employee_number or "—"),
        ("Department", report.user.department),
        ("Supervisor", report.supervisor_name),
        ("Title", report.title),
        ("Trip dates", trip_range_text),
        ("Status", report.get_status_display()),
        ("Created", report.created_at.strftime("%Y-%m-%d %H:%M")),
    ]:
        info_rows += 1
        sheet[f"A{info_rows}"], sheet[f"B{info_rows}"] = label, value

    if report.reviewed_at:
        info_rows += 1
        sheet[f"A{info_rows}"], sheet[f"B{info_rows}"] = "Reviewed", report.reviewed_at.strftime("%Y-%m-%d %H:%M")
        info_rows += 1
        sheet[f"A{info_rows}"], sheet[f"B{info_rows}"] = "Review note", report.review_note
        if report.approval_clause:
            info_rows += 1
            sheet[f"A{info_rows}"], sheet[f"B{info_rows}"] = "Approval clause", report.approval_clause

    header_row = info_rows + 2
    headers = ["#", "Type", "Date", "File", "Amount"]
    for col, text in enumerate(headers, start=1):
        cell = sheet.cell(row=header_row, column=col, value=text)
        cell.font = Font(bold=True)
        cell.fill = HEADER_FILL

    row = header_row + 1
    total = 0
    for index, doc in enumerate(report.documents.order_by("type", "document_date"), start=1):
        sheet.cell(row=row, column=1, value=index)
        sheet.cell(row=row, column=2, value=doc.get_type_display())
        sheet.cell(row=row, column=3, value=doc.document_date.strftime("%Y-%m-%d"))
        sheet.cell(row=row, column=4, value=doc.file_name)
        sheet.cell(row=row, column=5, value=float(doc.amount))
        total += doc.amount
        row += 1

    sheet.cell(row=row, column=4, value="Total").font = Font(bold=True)
    sheet.cell(row=row, column=5, value=float(total)).font = Font(bold=True)
    row += 2

    # Daily breakdown against the $60/day policy.
    sheet.cell(row=row, column=1, value=f"Daily breakdown (policy limit: ${DAILY_LIMIT_USD}/day)").font = Font(bold=True)
    row += 1
    daily_header_row = row
    for col, text in enumerate(["Date", "Daily total", "Over policy limit?"], start=1):
        cell = sheet.cell(row=daily_header_row, column=col, value=text)
        cell.font = Font(bold=True)
        cell.fill = HEADER_FILL
    row += 1
    for day in report.daily_totals():
        sheet.cell(row=row, column=1, value=day["date"].strftime("%Y-%m-%d"))
        sheet.cell(row=row, column=2, value=float(day["total"]))
        if day["over_limit"]:
            flag_value, fill = "Yes", VIOLATION_FILL
        elif day["has_flight_or_hotel"]:
            flag_value, fill = "Flight/Hotel", JUSTIFIED_FILL
        else:
            flag_value, fill = "No", None
        sheet.cell(row=row, column=3, value=flag_value)
        if fill:
            for col in (1, 2, 3):
                sheet.cell(row=row, column=col).fill = fill
        row += 1

    for col in "ABCDE":
        sheet.column_dimensions[col].width = 26

    return wb
