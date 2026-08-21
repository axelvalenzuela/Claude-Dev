"""The approval queue: ExpenseReportAdmin, the main working interface an
admin (department-scoped or HR/general) uses to review and approve/reject
submitted reports."""
from django.contrib import admin
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import path
from django.utils.html import format_html

from ..exporters import excel_exporter, history_exporter, word_exporter
from ..models import ExpenseReport, ExpenseReportAuditLog, log_action
from ..naming import export_basename
from ..policies import DAILY_LIMIT_USD
from ..receipt_capture import render_receipt_thumbnail
from ..services import finalize_approval
from .decorators import staff_permission
from .forms import ExpenseReportAdminForm
from .inlines import AuditLogInline, TravelDocumentInline
from .mixins import ExpenseReportDisplayMixin


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
    )
    # Split into two fieldsets — not just for visual grouping, but because
    # templates/admin/expenses/expensereport/change_form.html classifies
    # each rendered <fieldset> into a tab by its <h2> title text ("Report" /
    # "Review"), same as it does for the two inlines below ("Travel
    # documents" -> Documents, "Audit log entries" -> History). The
    # Excel/Word download links used to be a field here (exports_display);
    # they're now part of the Summary tab instead, rendered straight from
    # `original` in that same template, alongside an HTML preview of the
    # same data — important enough to not be one tab click away, and to be
    # checkable without opening either file.
    fieldsets = (
        ("Report", {
            "fields": (
                "user", "employee_number", "title", "description",
                "supervisor_name", "supervisor_email", "created_at",
            ),
        }),
        ("Review", {
            "fields": (
                "status", "review_note", "ceo_clause_ack", "approval_clause",
                "trip_date_range_display", "trip_start_date", "submission_deadline",
                "submitted_at", "reviewed_at", "reviewed_by",
                "total_amount_display", "daily_breakdown_display",
            ),
        }),
    )
    inlines = [TravelDocumentInline, AuditLogInline]

    def get_urls(self):
        # Two extra routes so an admin can preview/download Excel and Word
        # for a report that hasn't been approved yet — before this, the
        # Summary tab only had something to show once excel_snapshot/
        # word_snapshot existed (i.e. after approval), even though the
        # employee's own portal has always been able to generate a live
        # preview on demand (views/exports.py). Scoped through get_queryset
        # like everything else here — a department admin can preview their
        # own department's pending reports, never another's.
        custom_urls = [
            path(
                "<int:pk>/preview-excel/",
                self.admin_site.admin_view(self.preview_excel),
                name="expenses_expensereport_preview_excel",
            ),
            path(
                "<int:pk>/preview-word/",
                self.admin_site.admin_view(self.preview_word),
                name="expenses_expensereport_preview_word",
            ),
            path(
                "<int:pk>/documents/<int:doc_id>/preview-capture/",
                self.admin_site.admin_view(self.preview_receipt_capture),
                name="expenses_expensereport_preview_capture",
            ),
            path(
                "<int:pk>/download-history/",
                self.admin_site.admin_view(self.download_history),
                name="expenses_expensereport_download_history",
            ),
        ]
        return custom_urls + super().get_urls()

    def _get_scoped_report(self, request, pk):
        return get_object_or_404(self.get_queryset(request), pk=pk)

    def preview_receipt_capture(self, request, pk, doc_id):
        # Same PDF/photo-to-image rendering used to build the Word export's
        # "Receipt captures" section (receipt_capture.py) — lets an admin
        # see what a receipt actually looks like right in the browser,
        # without downloading anything, for as long as the original file
        # is still on the server (i.e. before the report is approved).
        report = self._get_scoped_report(request, pk)
        document = get_object_or_404(report.documents, pk=doc_id)
        if not document.file:
            raise Http404
        return HttpResponse(render_receipt_thumbnail(document.file), content_type="image/png")

    def preview_excel(self, request, pk):
        report = self._get_scoped_report(request, pk)
        response = HttpResponse(content_type=excel_exporter.content_type)
        response["Content-Disposition"] = f'inline; filename="{export_basename(report)}.{excel_exporter.extension}"'
        response.write(excel_exporter.to_bytes(report))
        return response

    def preview_word(self, request, pk):
        report = self._get_scoped_report(request, pk)
        response = HttpResponse(content_type=word_exporter.content_type)
        response["Content-Disposition"] = f'inline; filename="{export_basename(report)}.{word_exporter.extension}"'
        response.write(word_exporter.to_bytes(report))
        return response

    def download_history(self, request, pk):
        # Repurposes the object-tools slot Django's own "History" link used
        # to occupy (see templates/admin/expenses/expensereport/
        # change_form_object_tools.html) — a raw LogEntry page wasn't useful
        # here, but a downloadable timeline of every status change and
        # review note is. Always a live build (never gated on approval, and
        # never a saved snapshot), since the point is what's happened so far.
        report = self._get_scoped_report(request, pk)
        response = HttpResponse(content_type=history_exporter.content_type)
        filename = f"{export_basename(report)}_historial.{history_exporter.extension}"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response.write(history_exporter.to_bytes(report))
        return response

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

    # Any admin account (HR or a department admin) can open this app and
    # see the changeform — WHICH reports they can actually see/act on is
    # entirely decided by get_queryset() above, not by Django's permission
    # system (a department admin has no explicit "view_expensereport"
    # Permission object; is_staff plus the queryset scoping is the whole
    # model). All three checks are identical, so @staff_permission (see
    # ../decorators.py) writes that once instead of three times.
    @staff_permission
    def has_module_permission(self, request):
        ...

    @staff_permission
    def has_view_permission(self, request, obj=None):
        ...

    @staff_permission
    def has_change_permission(self, request, obj=None):
        ...

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
        # A full day-by-day table here just repeats what the Summary tab's
        # own daily breakdown already shows in more space — this field is
        # for a fast "is there anything to flag" read while reviewing, not
        # a second copy of the same table. Nothing to say unless a day
        # actually violates the policy.
        if not obj.pk:
            return "—"
        violations = [day for day in obj.daily_totals() if day["over_limit"]]
        if not violations:
            return format_html('<span style="color:#2e7d32;">&#10003; No policy violations</span>')
        notes = ", ".join(f'{day["date"]:%b %d} (${day["total_usd"]:.2f} USD)' for day in violations)
        return format_html(
            '<span style="color:#b02a37;font-weight:bold;">&#9888; {} day{} over $60/day: {}</span>',
            len(violations), "" if len(violations) == 1 else "s", notes,
        )

    daily_breakdown_display.short_description = f"$60/day policy check"

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

            if obj.status == ExpenseReport.Status.APPROVED:
                # Generates the final, RH-named Excel/Word exports and
                # removes the original receipt files — see
                # services.finalize_approval. Runs inside the same
                # transaction as this save (Django admin wraps the whole
                # changeform POST in one), so a failure here rolls the
                # approval back too, rather than leaving it half-done.
                finalize_approval(obj, request.user)

    def has_add_permission(self, request):
        return False
