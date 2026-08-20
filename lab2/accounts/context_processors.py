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
