"""Seeds Karen Plascencia's admin account: general admin (is_superuser=True,
same tier as Iris Cortez), approves reports from every department.

Password is a dev-only PLACEHOLDER default, same convention as 0002/0007/
0008 (overridable via KAREN_ADMIN_* in .env before the first `migrate`) —
the actual randomly-generated password lives only in .env (gitignored),
not committed here.
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


def seed_karen_admin(apps, schema_editor):
    User = apps.get_model("accounts", "User")

    email = os.environ.get("KAREN_ADMIN_EMAIL", "karen.plascencia@mhp.com")
    if User.objects.filter(email=email).exists():
        return

    User.objects.create(
        username=email,
        email=email,
        first_name=os.environ.get("KAREN_ADMIN_NAME", "Karen Plascencia"),
        department=os.environ.get("KAREN_ADMIN_DEPARTMENT", "Finance"),
        supervised_department="",
        password=make_password(os.environ.get("KAREN_ADMIN_PASSWORD", "ChangeMe#2026Local")),
        employee_number=_generate_employee_number(User),
        is_staff=True,
        is_superuser=True,
        is_active=True,
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("accounts", "0008_seed_axel_mhp_admin")]
    operations = [migrations.RunPython(seed_karen_admin, noop)]
