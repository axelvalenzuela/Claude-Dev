"""Assigns a random employee number (7 digits, e.g. 2490198) to every
existing user that doesn't have one yet — covers both real accounts created
before this field existed and the seeded admin account."""
import random

from django.db import migrations

EMPLOYEE_NUMBER_LENGTH = 7


def backfill_employee_numbers(apps, schema_editor):
    User = apps.get_model("accounts", "User")

    taken = set(
        User.objects.exclude(employee_number=None).values_list("employee_number", flat=True)
    )

    for user in User.objects.filter(employee_number=None):
        while True:
            candidate = str(random.randint(10 ** (EMPLOYEE_NUMBER_LENGTH - 1), 10**EMPLOYEE_NUMBER_LENGTH - 1))
            if candidate not in taken:
                taken.add(candidate)
                break
        user.employee_number = candidate
        user.save(update_fields=["employee_number"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [("accounts", "0004_user_employee_number")]
    operations = [migrations.RunPython(backfill_employee_numbers, noop)]
