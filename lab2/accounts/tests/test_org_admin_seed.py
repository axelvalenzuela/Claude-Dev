"""The migrations that seed the org-chart admin accounts — Iris Cortez
(HR), Adrian Heymes (ICS), Axel Valenzuela's MHP-domain admin identity, and
Karen Plascencia (HR/general) — always run for the test database, so we can
assert on their result directly. None of these assert on password values:
.env is loaded by settings.py before migrations run, so the test database
is actually seeded with whatever real password is in .env, not each
migration's committed placeholder default — see accounts/migrations/
0008_seed_axel_mhp_admin.py and 0009_seed_karen_admin.py for why the
committed defaults are deliberately not the real passwords."""
from django.test import TestCase

from accounts.models import User


class OrgAdminSeedTests(TestCase):
    def test_hr_admin_is_a_superuser_with_no_department_scope(self):
        iris = User.objects.get(email="iris.cortez@mhp.com")
        self.assertTrue(iris.is_staff)
        self.assertTrue(iris.is_superuser)
        self.assertEqual(iris.supervised_department, "")
        self.assertIsNotNone(iris.employee_number)

    def test_ics_admin_is_scoped_to_ics_only(self):
        adrian = User.objects.get(email="adrian.heymes@mhp.com")
        self.assertTrue(adrian.is_staff)
        self.assertFalse(adrian.is_superuser)
        self.assertEqual(adrian.supervised_department, "ICS")
        self.assertIsNotNone(adrian.employee_number)

    def test_org_admins_get_distinct_employee_numbers(self):
        iris = User.objects.get(email="iris.cortez@mhp.com")
        adrian = User.objects.get(email="adrian.heymes@mhp.com")
        self.assertNotEqual(iris.employee_number, adrian.employee_number)

    def test_axel_mhp_admin_is_a_superuser_with_no_department_scope(self):
        axel = User.objects.get(email="axel.valenzuela@mhp.com")
        self.assertTrue(axel.is_staff)
        self.assertTrue(axel.is_superuser)
        self.assertEqual(axel.supervised_department, "")
        self.assertIsNotNone(axel.employee_number)

    def test_karen_is_a_superuser_with_no_department_scope(self):
        karen = User.objects.get(email="karen.plascencia@mhp.com")
        self.assertTrue(karen.is_staff)
        self.assertTrue(karen.is_superuser)
        self.assertEqual(karen.supervised_department, "")
        self.assertIsNotNone(karen.employee_number)

    def test_every_seeded_admin_has_a_distinct_employee_number(self):
        numbers = list(
            User.objects.filter(
                email__in=[
                    "iris.cortez@mhp.com",
                    "adrian.heymes@mhp.com",
                    "axel.valenzuela@mhp.com",
                    "karen.plascencia@mhp.com",
                ]
            ).values_list("employee_number", flat=True)
        )
        self.assertEqual(len(numbers), 4)
        self.assertEqual(len(set(numbers)), 4)
