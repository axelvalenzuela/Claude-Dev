"""The migration that seeds Iris Cortez (HR) and Adrian Heymes (ICS) always
runs for the test database, so we can assert on its result directly."""
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
