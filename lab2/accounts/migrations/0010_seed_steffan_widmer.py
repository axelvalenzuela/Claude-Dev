"""Seeds Steffan Widmer's admin account: general admin (is_superuser=True,
same tier as Iris Cortez and Karen Plascencia). He's the CEO whose
delegated authority already backs every approval-clause acknowledgment
(expenses/policies.py:CEO_NAME) — this gives him an actual login to match,
so he's a real fourth person an employee can personally ask for admin
access, not just a name in approval text.

Password is a dev-only default, same convention as 0002/0007/0009
(overridable via STEFFAN_ADMIN_* in .env before the first `migrate`).
"""
import os
import random

from django.contrib.auth.hashers import make_password
from django.db import migrations

EMPLOYEE_NUMBER_LENGTH = 7


def _generate_employee_number(User):
    while True:
        candidate = str(random.randint(10 ** (EMPLOYEE_NUMBER_LENGTH - 1), 10**EMPLOYEE_NUMBER_LENGTH - 1))
        if not User.objects.filter(employee_number=candidate).exists():
            return candidate


def seed_steffan_widmer(apps, schema_editor):
    User = apps.get_model("accounts", "User")

    email = os.environ.get("STEFFAN_ADMIN_EMAIL", "steffan.widmer@mhp.com")
    if User.objects.filter(email=email).exists():
        return

    User.objects.create(
        username=email,
        email=email,
        first_name=os.environ.get("STEFFAN_ADMIN_NAME", "Steffan Widmer"),
        department=os.environ.get("STEFFAN_ADMIN_DEPARTMENT", "Executive"),
        supervised_department="",
        password=make_password(os.environ.get("STEFFAN_ADMIN_PASSWORD", "Steffan#2026Local")),
        employee_number=_generate_employee_number(User),
        is_staff=True,
        is_superuser=True,
        is_active=True,
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("accounts", "0009_seed_karen_admin")]
    operations = [migrations.RunPython(seed_steffan_widmer, noop)]
