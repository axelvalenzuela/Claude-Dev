import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .excel import build_report_workbook
from .forms import ExpenseReportForm, TravelDocumentForm
from .models import ExpenseReport, TravelDocument


def _owned_report(request, pk):
    return get_object_or_404(ExpenseReport, pk=pk, user=request.user)


@login_required
def report_list(request):
    reports = request.user.expense_reports.all()
    return render(request, "expenses/report_list.html", {"reports": reports})


@login_required
def report_create(request):
    if request.method == "POST":
        form = ExpenseReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user
            report.save()
            return redirect("reports:detail", pk=report.pk)
    else:
        form = ExpenseReportForm()
    return render(request, "expenses/report_form.html", {"form": form})


@login_required
def report_detail(request, pk):
    report = _owned_report(request, pk)
    upload_form = TravelDocumentForm()
    return render(
        request, "expenses/report_detail.html", {"report": report, "upload_form": upload_form}
    )


@login_required
def upload_document(request, pk):
    report = _owned_report(request, pk)

    if report.status != ExpenseReport.Status.DRAFT:
        messages.error(request, "Solo puedes agregar documentos mientras el reporte está en borrador.")
        return redirect("reports:detail", pk=pk)

    if request.method == "POST":
        form = TravelDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.expense_report = report
            document.save()
            messages.success(request, "Documento agregado.")
        else:
            errors = "; ".join(f"{field}: {', '.join(errs)}" for field, errs in form.errors.items())
            messages.error(request, f"No se pudo subir el documento: {errors}")

    return redirect("reports:detail", pk=pk)


@login_required
def delete_document(request, pk, doc_id):
    report = _owned_report(request, pk)

    if report.status != ExpenseReport.Status.DRAFT:
        messages.error(request, "Solo puedes eliminar documentos mientras el reporte está en borrador.")
        return redirect("reports:detail", pk=pk)

    document = get_object_or_404(TravelDocument, pk=doc_id, expense_report=report)
    document.file.delete(save=False)
    document.delete()
    return redirect("reports:detail", pk=pk)


@login_required
def submit_report(request, pk):
    report = _owned_report(request, pk)
    try:
        report.submit()
        report.save()
        messages.success(request, "Reporte enviado a revisión.")
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
    return redirect("reports:detail", pk=pk)


@login_required
def export_excel(request, pk):
    report = _owned_report(request, pk)
    return _excel_response(report)


def _excel_response(report):
    workbook = build_report_workbook(report)
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = f'attachment; filename="reporte-gastos-{report.pk}.xlsx"'
    workbook.save(response)
    return response


@login_required
def download_document(request, pk, doc_id):
    report = _owned_report(request, pk)
    document = get_object_or_404(TravelDocument, pk=doc_id, expense_report=report)
    if not document.file:
        raise Http404
    return FileResponse(
        document.file.open("rb"), as_attachment=True, filename=os.path.basename(document.file.name)
    )
