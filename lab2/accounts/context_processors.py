"""Template context processors shared across the whole site."""


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

    pending = ExpenseReport.objects.filter(status=ExpenseReport.Status.SUBMITTED)
    scoped_to_department = None

    if not user.is_superuser and user.supervised_department:
        pending = pending.filter(user__department=user.supervised_department)
        scoped_to_department = user.supervised_department

    return {
        "pending_reports_count": pending.count(),
        "pending_reports_scoped_to_department": scoped_to_department,
    }


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

    approved_count = reviewed.filter(status=ExpenseReport.Status.APPROVED).count()
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
    }


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
