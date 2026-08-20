import os
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone


def validate_file_size(file):
    max_mb = 10
    if file.size > max_mb * 1024 * 1024:
        raise ValidationError(f"El archivo excede el tamaño máximo de {max_mb} MB.")


def document_upload_path(instance, filename):
    # Nombre físico único (evita colisiones/renombrados silenciosos); el
    # nombre original se conserva aparte en original_filename para mostrarlo.
    ext = os.path.splitext(filename)[1]
    return f"uploads/{instance.expense_report.user_id}/{instance.expense_report_id}/{uuid.uuid4().hex}{ext}"


class ExpenseReport(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Borrador"
        SUBMITTED = "submitted", "En revisión"
        APPROVED = "approved", "Aprobado"
        REJECTED = "rejected", "Rechazado"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="expense_reports"
    )
    title = models.CharField("Título", max_length=150)
    description = models.TextField("Descripción", blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    created_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_reports",
    )
    review_note = models.TextField("Nota de revisión", blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def total_amount(self) -> Decimal:
        return sum((doc.amount for doc in self.documents.all()), Decimal("0"))

    # --- Reglas de negocio del flujo de aprobación --------------------------
    # Encapsuladas aquí (no en las vistas) para poder probarlas sin base de datos.

    def submit(self):
        if self.status != self.Status.DRAFT:
            raise ValidationError("Solo un reporte en borrador puede enviarse a revisión.")
        if not self.documents.exists():
            raise ValidationError("Agrega al menos un documento antes de enviar el reporte.")
        self.status = self.Status.SUBMITTED
        self.submitted_at = timezone.now()

    def approve(self, reviewer, note=""):
        if self.status != self.Status.SUBMITTED:
            raise ValidationError("Solo un reporte enviado a revisión puede aprobarse.")
        self.status = self.Status.APPROVED
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewer
        self.review_note = note

    def reject(self, reviewer, note):
        if self.status != self.Status.SUBMITTED:
            raise ValidationError("Solo un reporte enviado a revisión puede rechazarse.")
        if not note or not note.strip():
            raise ValidationError("Debes indicar un motivo de rechazo.")
        self.status = self.Status.REJECTED
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewer
        self.review_note = note


class TravelDocument(models.Model):
    class DocType(models.TextChoices):
        VUELO = "vuelo", "Vuelo"
        HOTEL = "hotel", "Hotel"
        TRANSPORTE = "transporte", "Transporte"
        ALIMENTOS = "alimentos", "Alimentos"
        OTRO = "otro", "Otro"

    expense_report = models.ForeignKey(
        ExpenseReport, on_delete=models.CASCADE, related_name="documents"
    )
    file = models.FileField(
        "Archivo",
        upload_to=document_upload_path,
        validators=[
            FileExtensionValidator(["pdf", "jpg", "jpeg", "png"]),
            validate_file_size,
        ],
    )
    original_filename = models.CharField(max_length=255, blank=True)
    type = models.CharField("Tipo", max_length=20, choices=DocType.choices)
    amount = models.DecimalField("Monto", max_digits=10, decimal_places=2)
    document_date = models.DateField("Fecha del gasto")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["document_date"]

    def __str__(self):
        return self.file_name

    def save(self, *args, **kwargs):
        if not self.original_filename and self.file:
            self.original_filename = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    @property
    def file_name(self) -> str:
        return self.original_filename or (os.path.basename(self.file.name) if self.file else "")
