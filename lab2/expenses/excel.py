"""Generación del reporte de gastos de viaje en Excel (.xlsx) a partir de un ExpenseReport."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

HEADER_FILL = PatternFill("solid", fgColor="D9D9D9")


def build_report_workbook(report) -> Workbook:
    wb = Workbook()
    sheet = wb.active
    sheet.title = "Reporte de gastos"

    sheet["A1"] = "Reporte de gastos de viaje"
    sheet["A1"].font = Font(bold=True, size=14)

    sheet["A3"], sheet["B3"] = "Empleado", report.user.get_full_name() or report.user.email
    sheet["A4"], sheet["B4"] = "Departamento", report.user.department
    sheet["A5"], sheet["B5"] = "Título", report.title
    sheet["A6"], sheet["B6"] = "Estado", report.get_status_display()
    sheet["A7"], sheet["B7"] = "Fecha de creación", report.created_at.strftime("%Y-%m-%d %H:%M")

    info_rows = 7
    if report.reviewed_at:
        sheet["A8"], sheet["B8"] = "Revisado", report.reviewed_at.strftime("%Y-%m-%d %H:%M")
        sheet["A9"], sheet["B9"] = "Nota de revisión", report.review_note
        info_rows = 9

    header_row = info_rows + 2
    headers = ["#", "Tipo", "Fecha", "Archivo", "Monto"]
    for col, text in enumerate(headers, start=1):
        cell = sheet.cell(row=header_row, column=col, value=text)
        cell.font = Font(bold=True)
        cell.fill = HEADER_FILL

    row = header_row + 1
    total = 0
    for index, doc in enumerate(report.documents.order_by("document_date"), start=1):
        sheet.cell(row=row, column=1, value=index)
        sheet.cell(row=row, column=2, value=doc.get_type_display())
        sheet.cell(row=row, column=3, value=doc.document_date.strftime("%Y-%m-%d"))
        sheet.cell(row=row, column=4, value=doc.file_name)
        sheet.cell(row=row, column=5, value=float(doc.amount))
        total += doc.amount
        row += 1

    sheet.cell(row=row, column=4, value="Total").font = Font(bold=True)
    sheet.cell(row=row, column=5, value=float(total)).font = Font(bold=True)

    for col in "ABCDE":
        sheet.column_dimensions[col].width = 24

    return wb
