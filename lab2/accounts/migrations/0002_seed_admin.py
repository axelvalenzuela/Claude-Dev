"""Creates, on the first `migrate`, the bootstrap account with /admin/ access.

Values come from environment variables so no credentials are hardcoded in
the source; if they're not set, local development defaults are used (see
this lab's README).
"""
import os

from django.contrib.auth.hashers import make_password
from django.db import migrations


def seed_admin(apps, schema_editor):
    User = apps.get_model("accounts", "User")

    email = os.environ.get("ADMIN_SEED_EMAIL", "axel.valenzuela@uabc.edu.mx")
    if User.objects.filter(email=email).exists():
        return

    password = os.environ.get("ADMIN_SEED_PASSWORD", "Admin#2026Local")
    full_name = os.environ.get("ADMIN_SEED_NAME", "Axel Valenzuela")
    department = os.environ.get("ADMIN_SEED_DEPARTMENT", "Administracion")

    User.objects.create(
        username=email,
        email=email,
        first_name=full_name,
        department=department,
        password=make_password(password),
        is_staff=True,
        is_superuser=True,
        is_active=True,
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    operations = [migrations.RunPython(seed_admin, noop)]
