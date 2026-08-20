"""Seeds the two named admin accounts from the company's org chart:

- Iris Cortez: the general/HR admin. is_superuser=True, so she can see and
  approve submitted reports from every department — she's the final,
  catch-all approver.
- Adrian Heymes: the ICS department admin. is_staff=True but NOT a
  superuser; supervised_department="ICS" scopes him to only see and approve
  reports from employees in that one department (see
  expenses/admin.py:ExpenseReportAdmin.get_queryset).

Both get a random employee number, same as any other account. Passwords are
dev-only defaults (see README) — change them before using this outside a
local machine.
"""
import os
import random

from django.contrib.auth.hashers import make_password
from django.db import migrations

EMPLOYEE_NUMBER_LENGTH = 7

ORG_ADMINS = [
    {
        "env_prefix": "HR_ADMIN",
        "email_default": "iris.cortez@mhp.com",
        "name_default": "Iris Cortez",
        "department_default": "Human Resources",
        "password_default": "Iris#2026Local",
        "is_superuser": True,
        "supervised_department": "",
    },
    {
        "env_prefix": "ICS_ADMIN",
        "email_default": "adrian.heymes@mhp.com",
        "name_default": "Adrian Heymes",
        "department_default": "ICS",
        "password_default": "Adrian#2026Local",
        "is_superuser": False,
        "supervised_department": "ICS",
    },
]


def _generate_employee_number(User):
    while True:
        candidate = str(random.randint(10 ** (EMPLOYEE_NUMBER_LENGTH - 1), 10**EMPLOYEE_NUMBER_LENGTH - 1))
        if not User.objects.filter(employee_number=candidate).exists():
            return candidate


def seed_org_admins(apps, schema_editor):
    User = apps.get_model("accounts", "User")

    for admin in ORG_ADMINS:
        email = os.environ.get(f"{admin['env_prefix']}_EMAIL", admin["email_default"])
        if User.objects.filter(email=email).exists():
            continue

        User.objects.create(
            username=email,
            email=email,
            first_name=os.environ.get(f"{admin['env_prefix']}_NAME", admin["name_default"]),
            department=os.environ.get(f"{admin['env_prefix']}_DEPARTMENT", admin["department_default"]),
            supervised_department=admin["supervised_department"],
            password=make_password(os.environ.get(f"{admin['env_prefix']}_PASSWORD", admin["password_default"])),
            employee_number=_generate_employee_number(User),
            is_staff=True,
            is_superuser=admin["is_superuser"],
            is_active=True,
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("accounts", "0006_user_supervised_department")]
    operations = [migrations.RunPython(seed_org_admins, noop)]
