"""The approval queue: ExpenseReportAdmin, the main working interface an
admin (department-scoped or HR/general) uses to review and approve/reject
submitted reports."""
from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from ..models import ExpenseReport, ExpenseReportAuditLog, log_action
from ..policies import DAILY_LIMIT_USD
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
    # each rendered <fieldset> into a tab by its <h2> title text ("Cuenta"
    # / "Revisión"), same as it does for the two inlines below ("Travel
    # documents" -> Documentos, "Audit log entries" -> Historial). The
    # Excel/Word download links used to be a field here (exports_display);
    # they're now a highlighted panel above the tabs instead, rendered
    # straight from `original` in that same template — important enough to
    # not be one tab click away.
    fieldsets = (
        ("Cuenta", {
            "fields": (
                "user", "employee_number", "title", "description",
                "supervisor_name", "supervisor_email", "created_at",
            ),
        }),
        ("Revisión", {
            "fields": (
                "status", "review_note", "ceo_clause_ack", "approval_clause",
                "trip_date_range_display", "trip_start_date", "submission_deadline",
                "submitted_at", "reviewed_at", "reviewed_by",
                "total_amount_display", "daily_breakdown_display",
            ),
        }),
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
