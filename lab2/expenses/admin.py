from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (
    CEO_NAME,
    CEO_TITLE,
    DAILY_LIMIT_USD,
    ApprovedExpenseReport,
    ExpenseReport,
    ExpenseReportAuditLog,
    TravelDocument,
    log_action,
)


class ExpenseReportAdminForm(forms.ModelForm):
    """Validates, in the admin form itself, that a status change is legal:
    only a 'Submitted' report can be approved/rejected, rejecting requires a
    note, and approving requires ticking the CEO approval clause."""

    ceo_clause_ack = forms.BooleanField(
        required=False,
        label=f"I confirm this approval is issued under the authority of {CEO_NAME} ({CEO_TITLE})",
        help_text="Required to approve a report. Not needed to reject one.",
    )

    class Meta:
        model = ExpenseReport
        fields = ["status", "review_note", "ceo_clause_ack"]

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
            raise forms.ValidationError("You can only approve or reject a report that is 'Submitted'.")
        if new_status not in (ExpenseReport.Status.APPROVED, ExpenseReport.Status.REJECTED):
            raise forms.ValidationError("From here you can only change the status to Approved or Rejected.")
        if new_status == ExpenseReport.Status.REJECTED and not note.strip():
            raise forms.ValidationError("You must provide a note/reason to reject the report.")
        if new_status == ExpenseReport.Status.APPROVED and not cleaned_data.get("ceo_clause_ack"):
            raise forms.ValidationError(
                f"You must confirm the CEO approval clause ({CEO_NAME}, {CEO_TITLE}) before approving."
            )

        return cleaned_data


class TravelDocumentInline(admin.TabularInline):
    model = TravelDocument
    extra = 0
    can_delete = False
    fields = (
        "type",
        "document_date",
        "amount",
        "file_link",
        "extracted_amount",
        "amount_mismatch",
        "detected_type",
        "type_mismatch",
        "uploaded_at",
    )
    readonly_fields = fields

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.file.url, obj.file_name)
        if obj.file_name:
            return format_html(
                '<span title="Original removed after submission">{} (archived — see Excel/Word)</span>',
                obj.file_name,
            )
        return "—"

    file_link.short_description = "File"

    def has_add_permission(self, request, obj=None):
        return False


class AuditLogInline(admin.TabularInline):
    model = ExpenseReportAuditLog
    extra = 0
    can_delete = False
    fields = ("created_at", "actor", "action", "note")
    readonly_fields = fields
    ordering = ["-created_at"]

    def has_add_permission(self, request, obj=None):
        return False


class ExpenseReportDisplayMixin:
    """Read-only display helpers shared by ExpenseReportAdmin (the working
    approval queue) and ApprovedExpenseReportAdmin (the approved-reports
    history) — both render the same kind of columns/fields, just with
    different querysets and permissions."""

    def employee(self, obj):
        return obj.user.get_full_name() or obj.user.email

    employee.short_description = "Employee"

    def employee_number(self, obj):
        return obj.user.employee_number or "—"

    employee_number.short_description = "Employee #"

    def department(self, obj):
        return obj.user.department

    def total_amount_display(self, obj):
        return f"${obj.total_amount:,.2f}"

    total_amount_display.short_description = "Total"

    def exports_display(self, obj):
        if not obj.excel_snapshot and not obj.word_snapshot:
            return "Not generated yet (report is still a draft)."
        links = []
        if obj.excel_snapshot:
            links.append(format_html('<a href="{}" target="_blank">Excel (.xlsx)</a>', obj.excel_snapshot.url))
        if obj.word_snapshot:
            links.append(format_html('<a href="{}" target="_blank">Word (.docx)</a>', obj.word_snapshot.url))
        return mark_safe(" · ".join(links))

    exports_display.short_description = "Archived exports"


@admin.register(ExpenseReport)
class ExpenseReportAdmin(ExpenseReportDisplayMixin, admin.ModelAdmin):
    """The approval interface: only accounts with /admin/ access (is_staff)
    reach this. Shows only reports that have actually been submitted —
    drafts stay private to the employee — ordered by submission date."""

    form = ExpenseReportAdminForm
    ordering = ["-submitted_at"]
    list_display = (
        "title",
        "employee",
        "employee_number",
        "department",
        "status",
        "total_amount_display",
        "policy_flag",
        "deadline_flag",
        "submitted_at",
    )
    list_filter = ("status",)
    search_fields = ("title", "user__first_name", "user__email", "user__employee_number")
    readonly_fields = (
        "user",
        "employee_number",
        "title",
        "description",
        "supervisor_name",
        "supervisor_email",
        "created_at",
        "submitted_at",
        "reviewed_at",
        "reviewed_by",
        "total_amount_display",
        "daily_breakdown_display",
        "trip_date_range_display",
        "trip_start_date",
        "submission_deadline",
        "approval_clause",
        "exports_display",
    )
    fields = (
        "user",
        "employee_number",
        "title",
        "description",
        "supervisor_name",
        "supervisor_email",
        "status",
        "review_note",
        "ceo_clause_ack",
        "approval_clause",
        "created_at",
        "submitted_at",
        "trip_date_range_display",
        "trip_start_date",
        "submission_deadline",
        "reviewed_at",
        "reviewed_by",
        "total_amount_display",
        "daily_breakdown_display",
        "exports_display",
    )
    inlines = [TravelDocumentInline, AuditLogInline]

    def get_queryset(self, request):
        # Drafts are private to the employee regardless of who's asking.
        queryset = super().get_queryset(request).exclude(status=ExpenseReport.Status.DRAFT)

        # HR / the general admin (is_superuser) sees every department. A
        # department admin (supervised_department set) only ever sees their
        # own department's reports — never another team's, even by guessing
        # a URL, since this scoping happens at the queryset level.
        if not request.user.is_superuser and request.user.supervised_department:
            queryset = queryset.filter(user__department=request.user.supervised_department)

        return queryset

    def has_module_permission(self, request):
        # Any admin account (HR or a department admin) can open this app —
        # WHICH reports they can see/act on is entirely decided by
        # get_queryset() above, not by Django's permission system (a
        # department admin has no explicit "view_expensereport" Permission
        # object; is_staff plus the queryset scoping is the whole model).
        return request.user.is_active and request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def trip_date_range_display(self, obj):
        trip_range = obj.trip_date_range
        if not trip_range:
            return "—"
        start, end = trip_range
        return f"{start:%Y-%m-%d} to {end:%Y-%m-%d}"

    trip_date_range_display.short_description = "Trip dates"

    def policy_flag(self, obj):
        if obj.has_policy_violations:
            return format_html('<span style="color:#b02a37;font-weight:bold;">⚠ Over $60/day</span>')
        return "OK"

    policy_flag.short_description = "Policy"

    def deadline_flag(self, obj):
        if obj.status == ExpenseReport.Status.DRAFT or obj.submission_deadline is None:
            return "—"
        if obj.is_past_deadline:
            return format_html('<span style="color:#b02a37;font-weight:bold;">Past deadline</span>')
        return obj.submission_deadline.strftime("%Y-%m-%d")

    deadline_flag.short_description = "Deadline"

    def daily_breakdown_display(self, obj):
        if not obj.pk:
            return "—"
        # Row content is built only from dates/decimals/fixed strings (no
        # user-controlled text), so it's safe to mark as pre-escaped HTML.
        rows = "".join(
            '<tr style="{bg}">'
            '<td style="padding:2px 8px;">{date:%Y-%m-%d}</td>'
            '<td style="padding:2px 8px;">${total:.2f}</td>'
            '<td style="padding:2px 8px;">{flag}</td>'
            "</tr>".format(
                bg="background:#f8d7da;" if day["over_limit"] else "",
                date=day["date"],
                total=day["total"],
                flag="⚠ Over limit" if day["over_limit"] else "OK",
            )
            for day in obj.daily_totals()
        )
        if not rows:
            return "No documents yet."
        return format_html(
            '<table style="border-collapse:collapse;">'
            '<tr style="font-weight:bold;"><td style="padding:2px 8px;">Date</td>'
            '<td style="padding:2px 8px;">Total</td><td style="padding:2px 8px;">$60/day policy</td></tr>'
            "{}</table>",
            mark_safe(rows),
        )

    daily_breakdown_display.short_description = f"Daily spend (policy: ${DAILY_LIMIT_USD}/day)"

    def save_model(self, request, obj, form, change):
        status_changed = change and "status" in form.changed_data

        if status_changed:
            # `obj` already carries the *new* status (the ModelForm applied
            # it before save_model runs), so the domain methods' "must be
            # submitted" guard would reject it. Run the transition against a
            # freshly-loaded copy (still in its pre-change state) instead,
            # then copy the result back onto `obj` for Django to persist.
            # form.clean() already validated legality (submitted-only,
            # required note/CEO ack), so this shouldn't raise in practice.
            original = ExpenseReport.objects.get(pk=obj.pk)
            note = form.cleaned_data.get("review_note", "")
            if obj.status == ExpenseReport.Status.APPROVED:
                original.approve(request.user, note, ceo_clause_ack=form.cleaned_data.get("ceo_clause_ack", False))
            elif obj.status == ExpenseReport.Status.REJECTED:
                original.reject(request.user, note)

            obj.status = original.status
            obj.reviewed_at = original.reviewed_at
            obj.reviewed_by = original.reviewed_by
            obj.review_note = original.review_note
            obj.ceo_authorized = original.ceo_authorized
            obj.approval_clause = original.approval_clause

        super().save_model(request, obj, form, change)

        if status_changed:
            action = (
                ExpenseReportAuditLog.Action.APPROVED
                if obj.status == ExpenseReport.Status.APPROVED
                else ExpenseReportAuditLog.Action.REJECTED
            )
            log_action(obj, request.user, action, obj.review_note)

    def has_add_permission(self, request):
        return False


@admin.register(ApprovedExpenseReport)
class ApprovedExpenseReportAdmin(ExpenseReportDisplayMixin, admin.ModelAdmin):
    """The "approved reports history" the admin can browse — a distinct,
    read-only section of Django Admin (not just a filter on the working
    queue), sorted alphabetically by title for quick lookup rather than by
    date. Approving/rejecting still only happens from ExpenseReportAdmin."""

    ordering = ["title"]
    list_display = ("title", "employee", "employee_number", "department", "total_amount_display", "reviewed_at")
    search_fields = ("title", "user__first_name", "user__email", "user__employee_number")
    readonly_fields = (
        "user",
        "employee_number",
        "title",
        "description",
        "supervisor_name",
        "supervisor_email",
        "status",
        "review_note",
        "approval_clause",
        "submitted_at",
        "reviewed_at",
        "reviewed_by",
        "total_amount_display",
        "exports_display",
    )
    fields = readonly_fields
    inlines = [TravelDocumentInline]

    def get_queryset(self, request):
        queryset = super().get_queryset(request).filter(status=ExpenseReport.Status.APPROVED)
        if not request.user.is_superuser and request.user.supervised_department:
            queryset = queryset.filter(user__department=request.user.supervised_department)
        return queryset

    def has_module_permission(self, request):
        return request.user.is_active and request.user.is_staff

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ExpenseReportAuditLog)
class ExpenseReportAuditLogAdmin(admin.ModelAdmin):
    """Read-only, full audit trail across all reports — the admin's
    traceability view of who did what, and when."""

    list_display = ("created_at", "report", "actor", "action", "note")
    list_filter = ("action",)
    search_fields = ("report__title", "actor__email", "note")
    readonly_fields = ("report", "actor", "action", "note", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
