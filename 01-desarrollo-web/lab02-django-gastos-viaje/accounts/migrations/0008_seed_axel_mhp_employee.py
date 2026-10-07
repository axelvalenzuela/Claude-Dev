"""Seeds Axel Valenzuela's company-domain account (axel.valenzuela@mhp.com),
alongside the existing bootstrap admin account
(axel.valenzuela@uabc.edu.mx, migration 0002) — but this one is a
**regular employee**, not an admin: is_staff=False, no admin-panel access.
It's the account used to exercise the employee side of the app (upload
receipts, submit a report, wait for one of the admins to approve it), kept
separate from the bootstrap account so testing "what does an employee
see" doesn't require logging out of the admin identity first.

Password is a dev-only PLACEHOLDER default, same convention as 0002/0007
(overridable via AXEL_MHP_EMPLOYEE_* in .env before the first `migrate`) —
deliberately NOT the actual password this account uses locally: that one
lives only in .env (gitignored, never committed), exactly so a real,
reused personal password never ends up sitting in git history the way a
committed migration default would.
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


def seed_axel_mhp_employee(apps, schema_editor):
    User = apps.get_model("accounts", "User")

    email = os.environ.get("AXEL_MHP_EMPLOYEE_EMAIL", "axel.valenzuela@mhp.com")
    if User.objects.filter(email=email).exists():
        return

    User.objects.create(
        username=email,
        email=email,
        first_name=os.environ.get("AXEL_MHP_EMPLOYEE_NAME", "Axel Valenzuela"),
        department=os.environ.get("AXEL_MHP_EMPLOYEE_DEPARTMENT", "ICS"),
        supervised_department="",
        password=make_password(os.environ.get("AXEL_MHP_EMPLOYEE_PASSWORD", "ChangeMe#2026Local")),
        employee_number=_generate_employee_number(User),
        is_staff=False,
        is_superuser=False,
        is_active=True,
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("accounts", "0007_seed_org_admins")]
    operations = [migrations.RunPython(seed_axel_mhp_employee, noop)]
