"""Template context processors shared across the whole site."""
from decimal import Decimal

from django.db.models import Q


def pending_reports_notification(request):
    """Feeds the "reports to review" notification banner shown to staff
    users on the Django Admin dashboard (see templates/admin/index.html).

    - HR / the general admin (is_superuser) sees the count across every
      department.
    - A department admin (is_staff, not superuser, with
      `supervised_department` set) only sees the count for their own
      department — they should never be prompted about reports outside
      their area.
    - Anyone else (regular employees, anonymous users) gets nothing; the
      template only renders the banner for staff users anyway.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or not user.is_staff:
        return {}

    # Local import avoids a circular import between accounts and expenses at
    # module load time (expenses doesn't depend on accounts.context_processors).
    from expenses.models import ExpenseReport

    pending = ExpenseReport.objects.filter(status=ExpenseReport.Status.SUBMITTED).select_related("user")
    scoped_to_department = None

    if not user.is_superuser and user.supervised_department:
        pending = pending.filter(user__department=user.supervised_department)
        scoped_to_department = user.supervised_department

    pending = list(pending.order_by("-submitted_at"))

    return {
        "pending_reports_count": len(pending),
        "pending_reports_scoped_to_department": scoped_to_department,
        # $ waiting on this admin's desk right now — feeds the dashboard
        # stat cards alongside the banner (see templates/admin/index.html).
        "pending_reports_amount_total": sum((r.total_amount for r in pending), Decimal("0")),
        # The actual rows, for the "pending review expenses" table on the
        # Dashboard tab — same scoping as the count/amount above.
        "pending_reports_list": pending,
    }


DASHBOARD_APPROVED_TABLE_LIMIT = 25


def approved_reports_table(request):
    """Feeds the "Approved" side of the Dashboard's expense-reports table
    (see templates/admin/index.html) — pending_reports_notification above
    already provides the "Pending" side (pending_reports_list); this is the
    same idea for reports that have already been approved, with the same
    department scoping, so an admin can filter between the two right on
    the Dashboard instead of opening the full Reports changelist."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or not user.is_staff:
        return {}

    from expenses.models import ExpenseReport

    approved = ExpenseReport.objects.filter(status=ExpenseReport.Status.APPROVED).select_related("user")
    if not user.is_superuser and user.supervised_department:
        approved = approved.filter(user__department=user.supervised_department)

    return {"approved_reports_list": list(approved.order_by("-reviewed_at")[:DASHBOARD_APPROVED_TABLE_LIMIT])}


def approval_chart(request):
    """Feeds the circular (donut) approved-vs-rejected chart on the admin
    dashboard — how much of what this admin has actually decided on was
    approved vs. sent back, scoped to their department the same way the
    notification banner and the approval queue are."""
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or not user.is_staff:
        return {}

    from expenses.models import ExpenseReport

    reviewed = ExpenseReport.objects.filter(
        status__in=[ExpenseReport.Status.APPROVED, ExpenseReport.Status.REJECTED]
    )
    if not user.is_superuser and user.supervised_department:
        reviewed = reviewed.filter(user__department=user.supervised_department)

    approved = list(reviewed.filter(status=ExpenseReport.Status.APPROVED))
    approved_count = len(approved)
    rejected_count = reviewed.filter(status=ExpenseReport.Status.REJECTED).count()
    total = approved_count + rejected_count

    # Percentage boundary for the CSS conic-gradient donut (0 when there's
    # nothing reviewed yet, so the chart just renders as an empty ring).
    approved_pct = round((approved_count / total) * 100) if total else 0

    return {
        "approval_chart_approved": approved_count,
        "approval_chart_rejected": rejected_count,
        "approval_chart_total": total,
        "approval_chart_approved_pct": approved_pct,
        "approval_chart_rejected_pct": 100 - approved_pct if total else 0,
        # Historical $ approved — feeds the dashboard stat cards.
        "approval_chart_approved_amount": sum((r.total_amount for r in approved), Decimal("0")),
    }


def employee_directory(request):
    """Feeds the searchable "Employees" tab in the admin — every employee
    registered on the platform (scoped by department like everything else
    here), whether or not they've ever submitted a report, so RH can look
    someone up before they've done anything, not only after. Each entry
    also carries their report count and most recent report (if any), so the
    template can tell apart "has a pending review expense" (needs
    attention) from "only resolved/no reports" (nothing to do) without
    querying again.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or not user.is_staff:
        return {}

    from .models import User
    from expenses.models import ExpenseReport

    reports = ExpenseReport.objects.exclude(status=ExpenseReport.Status.DRAFT).select_related("user")
    if not user.is_superuser and user.supervised_department:
        reports = reports.filter(user__department=user.supervised_department)

    by_employee_reports = {}
    for report in reports.order_by("-submitted_at"):
        by_employee_reports.setdefault(report.user_id, []).append(report)

    # "Employee" here means anyone who isn't themselves an approver — a
    # regular (non-staff) account, or a staff/superuser account that
    # happens to have submitted a report of their own (e.g. a bootstrap
    # admin account used for personal testing).
    employees = User.objects.filter(Q(is_staff=False) | Q(pk__in=by_employee_reports.keys())).distinct()
    if not user.is_superuser and user.supervised_department:
        employees = employees.filter(department=user.supervised_department)

    directory = []
    for employee in employees:
        employee_reports = by_employee_reports.get(employee.pk, [])
        latest_report = employee_reports[0] if employee_reports else None
        directory.append(
            {
                "employee": employee,
                "report_count": len(employee_reports),
                "latest_report": latest_report,
                "has_pending": bool(latest_report and latest_report.status == ExpenseReport.Status.SUBMITTED),
            }
        )

    directory.sort(key=lambda entry: (entry["employee"].get_full_name() or entry["employee"].email).lower())

    return {"employee_directory": directory}


def admin_scope_badge(request):
    """Feeds the "signed in as" role badge shown on every Django Admin page
    (see templates/admin/base_site.html branding block) — the only place in
    the UI that visually distinguishes the HR/general admin (is_superuser,
    sees every department) from a department-scoped admin (supervised_
    department set, sees only their own). Without it, the difference between
    the two admin roles is only observable indirectly, from which reports
    happen to show up in the queue.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or not user.is_staff:
        return {}

    if user.is_superuser:
        label = "HR administrator — all departments"
    elif user.supervised_department:
        label = f"{user.supervised_department} department administrator"
    else:
        label = "Administrator"

    return {"admin_scope_label": label}


RECENT_REVIEW_WINDOW_DAYS = 7


def recent_review_notification(request):
    """Feeds the "your report was approved/rejected" notification banner
    shown to employees across the portal (see templates/base.html) — the
    rejection note the admin left is included right there, so there's no
    separate place to go dig it out. Reports reviewed a while ago (see
    RECENT_REVIEW_WINDOW_DAYS) stop showing here; they're still visible
    permanently, with their note, on the History page.
    """
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated or user.is_staff:
        return {}

    from datetime import timedelta

    from django.utils import timezone

    from expenses.models import ExpenseReport

    cutoff = timezone.now() - timedelta(days=RECENT_REVIEW_WINDOW_DAYS)
    recent = list(
        user.expense_reports.filter(
            status__in=[ExpenseReport.Status.APPROVED, ExpenseReport.Status.REJECTED],
            reviewed_at__gte=cutoff,
        ).order_by("-reviewed_at")
    )

    return {"recent_review_notifications": recent}
