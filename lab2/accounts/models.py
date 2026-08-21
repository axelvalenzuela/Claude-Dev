"""The custom User model (email as username, department, employee number,
department-admin scope) and the LoginEvent audit trail every login attempt
is recorded into — the foundation both accounts/security.py's lockout and
the admin's traceability view build on top of."""
import random

from django.contrib.auth.models import AbstractUser
from django.db import models

EMPLOYEE_NUMBER_LENGTH = 7  # e.g. 2490198


def generate_employee_number() -> str:
    """A random, unique company employee number (7 digits, like 2490198).
    Assigned automatically — employees never type this in themselves."""
    while True:
        candidate = str(random.randint(10 ** (EMPLOYEE_NUMBER_LENGTH - 1), 10**EMPLOYEE_NUMBER_LENGTH - 1))
        if not User.objects.filter(employee_number=candidate).exists():
            return candidate


class User(AbstractUser):
    """App user. username = email; adds the employee's department, company
    employee number, and (for admin accounts only) the department they
    approve expense reports for.

    Two kinds of admin accounts exist (both are is_staff=True):
      - The general/HR admin (is_superuser=True) approves every report,
        regardless of department. There should only be one or two of these
        (seeded as Iris Cortez — see migration 0006_seed_org_admins).
      - A department admin (is_superuser=False, supervised_department set)
        only sees and approves reports from employees in that one
        department (enforced in expenses/admin.py's get_queryset and used
        for the "reports to review" notification). Seeded example: Adrian
        Heymes for the ICS department.
    """

    department = models.CharField("Department", max_length=100, blank=True)
    employee_number = models.CharField(
        "Employee number", max_length=20, unique=True, null=True, blank=True
    )
    supervised_department = models.CharField(
        "Supervises department (admin only)",
        max_length=100,
        blank=True,
        help_text=(
            "For a department admin: the one department whose submitted reports "
            "they can see and approve. Leave blank for regular employees and for "
            "the general/HR admin (who sees every department via is_superuser)."
        ),
    )

    def __str__(self):
        return self.get_full_name() or self.email or self.username


class LoginEvent(models.Model):
    """Session/login audit trail, for the admin's security & traceability view.

    Recorded for both successful and failed attempts (user is null on a
    failed attempt against an email that doesn't exist)."""

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="login_events")
    email_attempted = models.CharField(max_length=255)
    success = models.BooleanField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        status = "success" if self.success else "failed"
        return f"{self.email_attempted} · {status} · {self.created_at:%Y-%m-%d %H:%M}"
