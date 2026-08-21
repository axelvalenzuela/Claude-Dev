"""ORM models for the expense-report domain: ExpenseReport, TravelDocument,
and their supporting audit-log/proxy models.

The numeric policy limits and cross-report validation
(DAILY_LIMIT_USD, SUBMISSION_WINDOW_DAYS, MAX_TRIP_SPAN_DAYS, CEO_NAME,
validate_trip_span) live in policies.py, and the generic file-size
validator lives in validators.py — both imported below and used by
ExpenseReport's own methods, but kept in their own modules so the business
policy can be read (and changed) without wading through the schema, and
vice versa.
"""
import os
import uuid
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone

from .pdf_analysis import validate_pdf_page_count
from .policies import CEO_NAME, CEO_TITLE, DAILY_LIMIT_USD, SUBMISSION_WINDOW_DAYS
from .validators import validate_file_size


def document_upload_path(instance, filename):
    # Unique physical name (avoids silent renames on collision); the original
    # name is kept separately in original_filename for display/download.
    ext = os.path.splitext(filename)[1]
    return f"uploads/{instance.expense_report.user_id}/{instance.expense_report_id}/{uuid.uuid4().hex}{ext}"


class ExpenseReport(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="expense_reports"
    )
    title = models.CharField("Title", max_length=150)
    description = models.TextField("Description", blank=True)
    supervisor_name = models.CharField("Supervisor name", max_length=150, default="")
    supervisor_email = models.EmailField("Supervisor email", blank=True)
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
    review_note = models.TextField("Review note", blank=True)

    # Governance: every approval is issued under the CEO's delegated authority.
    ceo_authorized = models.BooleanField(default=False)
    approval_clause = models.CharField(max_length=255, blank=True)

    # Generated once, right when the report is submitted (see
    # expenses/services.py:finalize_submission), and kept permanently as the
    # retained record of the expense — see TravelDocument.file below for why
    # the *original* uploads don't stick around after that point.
    excel_snapshot = models.FileField(upload_to="reports/%Y/%m", blank=True)
    word_snapshot = models.FileField(upload_to="reports/%Y/%m", blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def total_amount(self) -> Decimal:
        return sum((doc.amount for doc in self.documents.all()), Decimal("0"))

    # --- Travel window / submission deadline --------------------------------

    @property
    def trip_start_date(self):
        """Reference date for the submission deadline: the earliest FLIGHT
        document's date, or the earliest document of any type if there is no
        flight on file yet."""
        flight_dates = [
            doc.document_date
            for doc in self.documents.all()
            if doc.type == TravelDocument.DocType.FLIGHT
        ]
        if flight_dates:
            return min(flight_dates)

        all_dates = [doc.document_date for doc in self.documents.all()]
        return min(all_dates) if all_dates else None

    @property
    def trip_date_range(self):
        """(first, last) expense date across every document — the trip's
        date range, for the enterprise-style summary header."""
        all_dates = [doc.document_date for doc in self.documents.all()]
        return (min(all_dates), max(all_dates)) if all_dates else None

    @property
    def submission_deadline(self):
        start = self.trip_start_date
        return start + timedelta(days=SUBMISSION_WINDOW_DAYS) if start else None

    @property
    def is_past_deadline(self) -> bool:
        deadline = self.submission_deadline
        return bool(deadline and timezone.now().date() > deadline)

    # --- $60/day expense policy ----------------------------------------------

    def daily_totals(self):
        """Per-day breakdown of requested expenses, flagging days over the
        company's daily limit (DAILY_LIMIT_USD)."""
        totals = defaultdict(lambda: Decimal("0"))
        for doc in self.documents.all():
            totals[doc.document_date] += doc.amount

        return [
            {"date": date, "total": total, "over_limit": total > DAILY_LIMIT_USD}
            for date, total in sorted(totals.items())
        ]

    @property
    def has_policy_violations(self) -> bool:
        return any(day["over_limit"] for day in self.daily_totals())

    # --- Approval workflow ----------------------------------------------------
    # Encapsulated here (not in views/admin) so the rules can be tested
    # without going through HTTP or the Django admin.

    def submit(self):
        if self.status != self.Status.DRAFT:
            raise ValidationError("Only a draft report can be submitted for review.")
        if not self.documents.exists():
            raise ValidationError("Add at least one document before submitting the report.")
        if self.is_past_deadline:
            raise ValidationError(
                f"Submission deadline has passed: reports must be submitted within "
                f"{SUBMISSION_WINDOW_DAYS} days of the flight date "
                f"({self.submission_deadline:%Y-%m-%d})."
            )

        self.status = self.Status.SUBMITTED
        self.submitted_at = timezone.now()

    def approve(self, reviewer, note="", ceo_clause_ack=False):
        if self.status != self.Status.SUBMITTED:
            raise ValidationError("Only a submitted report can be approved.")
        if not ceo_clause_ack:
            raise ValidationError(
                f"You must confirm the CEO approval clause ({CEO_NAME}, {CEO_TITLE}) before approving."
            )

        self.status = self.Status.APPROVED
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewer
        self.review_note = note
        self.ceo_authorized = True
        self.approval_clause = f"Approved under authority delegated by {CEO_NAME}, {CEO_TITLE}."

    def reject(self, reviewer, note):
        if self.status != self.Status.SUBMITTED:
            raise ValidationError("Only a submitted report can be rejected.")
        if not note or not note.strip():
            raise ValidationError("You must provide a reason for rejecting the report.")

        self.status = self.Status.REJECTED
        self.reviewed_at = timezone.now()
        self.reviewed_by = reviewer
        self.review_note = note


class TravelDocument(models.Model):
    class DocType(models.TextChoices):
        TAXI = "taxi", "Taxi"
        MEAL = "meal", "Meal"
        FLIGHT = "flight", "Flight"
        HOTEL = "hotel", "Hotel"
        OTHER = "other", "Other"

    expense_report = models.ForeignKey(
        ExpenseReport, on_delete=models.CASCADE, related_name="documents"
    )
    file = models.FileField(
        "File",
        upload_to=document_upload_path,
        blank=True,  # cleared once the report is submitted — see finalize_submission()
        validators=[
            FileExtensionValidator(["pdf", "jpg", "jpeg", "png"]),
            validate_file_size,
            validate_pdf_page_count,
        ],
    )
    original_filename = models.CharField(max_length=255, blank=True)
    type = models.CharField("Type", max_length=20, choices=DocType.choices)
    amount = models.DecimalField("Amount", max_digits=10, decimal_places=2)
    document_date = models.DateField("Expense date")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    # Best-effort PDF content analysis, run at upload time (see
    # expenses/pdf_analysis.py), to catch mistakes/policy issues early.
    extracted_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount_mismatch = models.BooleanField(default=False)
    detected_type = models.CharField(max_length=20, choices=DocType.choices, blank=True)
    type_mismatch = models.BooleanField(default=False)

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


class ExpenseReportAuditLog(models.Model):
    """Immutable trail of the key events in a report's lifecycle, for the
    admin's security/traceability view (who did what, and when)."""

    class Action(models.TextChoices):
        CREATED = "created", "Created"
        DOCUMENT_UPLOADED = "document_uploaded", "Document uploaded"
        DOCUMENT_DELETED = "document_deleted", "Document deleted"
        SUBMITTED = "submitted", "Submitted"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    report = models.ForeignKey(ExpenseReport, on_delete=models.CASCADE, related_name="audit_log")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+"
    )
    action = models.CharField(max_length=30, choices=Action.choices)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Audit log entry"
        verbose_name_plural = "Audit log entries"

    def __str__(self):
        return f"{self.report_id} · {self.action} · {self.created_at:%Y-%m-%d %H:%M}"


def log_action(report, actor, action, note=""):
    return ExpenseReportAuditLog.objects.create(report=report, actor=actor, action=action, note=note)


class ApprovedExpenseReport(ExpenseReport):
    """Proxy model with no fields of its own — same table as ExpenseReport,
    registered separately in Django Admin (see expenses/admin.py) so the
    "approved reports history" is its own browsable, read-only section
    instead of just a filter on the main approval queue."""

    class Meta:
        proxy = True
        verbose_name = "Approved report (history)"
        verbose_name_plural = "Approved reports (history)"
