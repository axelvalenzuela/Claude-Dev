from django import forms
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import ExpenseReport, TravelDocument


class ExpenseReportAdminForm(forms.ModelForm):
    """Valida en el propio formulario del admin que el cambio de estado sea legal:
    solo se puede aprobar/rechazar un reporte que esté 'En revisión', y rechazar
    exige una nota con el motivo."""

    class Meta:
        model = ExpenseReport
        fields = ["status", "review_note"]

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk:
            return cleaned_data

        current_status = ExpenseReport.objects.get(pk=self.instance.pk).status
        new_status = cleaned_data.get("status")
        note = cleaned_data.get("review_note") or ""

        if new_status == current_status:
            return cleaned_data

        if current_status != ExpenseReport.Status.SUBMITTED:
            raise forms.ValidationError("Solo puedes aprobar o rechazar reportes que estén 'En revisión'.")
        if new_status not in (ExpenseReport.Status.APPROVED, ExpenseReport.Status.REJECTED):
            raise forms.ValidationError("Desde aquí solo puedes cambiar el estado a Aprobado o Rechazado.")
        if new_status == ExpenseReport.Status.REJECTED and not note.strip():
            raise forms.ValidationError("Debes indicar una nota/motivo para rechazar el reporte.")

        return cleaned_data


class TravelDocumentInline(admin.TabularInline):
    model = TravelDocument
    extra = 0
    can_delete = False
    fields = ("type", "document_date", "amount", "file_link", "uploaded_at")
    readonly_fields = fields

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.file.url, obj.file_name)
        return "—"

    file_link.short_description = "Archivo"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(ExpenseReport)
class ExpenseReportAdmin(admin.ModelAdmin):
    """Interfaz de aprobación: solo cuentas con acceso a /admin/ (is_staff) llegan aquí.
    Muestra únicamente reportes ya enviados (los borradores son privados del empleado)."""

    form = ExpenseReportAdminForm
    list_display = ("title", "employee", "department", "status", "total_amount_display", "submitted_at")
    list_filter = ("status",)
    search_fields = ("title", "user__first_name", "user__email")
    readonly_fields = (
        "user",
        "title",
        "description",
        "created_at",
        "submitted_at",
        "reviewed_at",
        "reviewed_by",
        "total_amount_display",
    )
    fields = (
        "user",
        "title",
        "description",
        "status",
        "review_note",
        "created_at",
        "submitted_at",
        "reviewed_at",
        "reviewed_by",
        "total_amount_display",
    )
    inlines = [TravelDocumentInline]

    def get_queryset(self, request):
        return super().get_queryset(request).exclude(status=ExpenseReport.Status.DRAFT)

    def employee(self, obj):
        return obj.user.get_full_name() or obj.user.email

    employee.short_description = "Empleado"

    def department(self, obj):
        return obj.user.department

    def total_amount_display(self, obj):
        return f"${obj.total_amount:,.2f}"

    total_amount_display.short_description = "Total"

    def save_model(self, request, obj, form, change):
        if change and "status" in form.changed_data:
            obj.reviewed_at = timezone.now()
            obj.reviewed_by = request.user
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        return False
