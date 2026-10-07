"""Users & Groups access (accounts/admin.py:StaffManagedAdminMixin): any
active is_staff account can view/manage accounts and groups, not just the
HR/general (is_superuser) admin — granting someone admin access is a
personal request handled by whichever admin is asked (see the Dashboard's
Policies/Help tabs), department-scoped admins included."""
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class UsersGroupsAccessTests(TestCase):
    def test_department_admin_can_view_the_user_list(self):
        self.client.login(username="adrian.heymes@mhp.com", password="Adrian#2026Local")
        response = self.client.get(reverse("admin:accounts_user_changelist"))
        self.assertEqual(response.status_code, 200)

    def test_department_admin_can_view_the_group_list(self):
        self.client.login(username="adrian.heymes@mhp.com", password="Adrian#2026Local")
        response = self.client.get(reverse("admin:auth_group_changelist"))
        self.assertEqual(response.status_code, 200)

    def test_department_admin_can_grant_admin_access_to_someone(self):
        employee = User.objects.create_user(
            username="new.hire@example.com", email="new.hire@example.com", password="x", department="ICS"
        )
        self.client.login(username="adrian.heymes@mhp.com", password="Adrian#2026Local")

        url = reverse("admin:accounts_user_change", args=[employee.pk])
        response = self.client.post(
            url,
            {
                "username": employee.username,
                "email": employee.email,
                "first_name": "",
                "last_name": "",
                "department": "ICS",
                "supervised_department": "",
                "is_staff": "on",
                "is_active": "on",
                "date_joined_0": employee.date_joined.strftime("%Y-%m-%d"),
                "date_joined_1": employee.date_joined.strftime("%H:%M:%S"),
                "initial-date_joined_0": employee.date_joined.strftime("%Y-%m-%d"),
                "initial-date_joined_1": employee.date_joined.strftime("%H:%M:%S"),
                "_save": "Save",
            },
        )

        employee.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertTrue(employee.is_staff)

    def test_hr_admin_still_has_full_access(self):
        self.client.login(username="iris.cortez@mhp.com", password="Iris#2026Local")
        self.assertEqual(self.client.get(reverse("admin:accounts_user_changelist")).status_code, 200)
        self.assertEqual(self.client.get(reverse("admin:auth_group_changelist")).status_code, 200)

    def test_regular_employee_cannot_reach_user_admin(self):
        User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123", department="Sales"
        )
        self.client.login(username="ana@example.com", password="clave123")
        response = self.client.get(reverse("admin:accounts_user_changelist"))
        self.assertEqual(response.status_code, 302)  # redirects to admin login

    def test_group_model_is_registered_under_the_custom_admin(self):
        from accounts.admin import GroupAdmin
        from django.contrib import admin

        self.assertIsInstance(admin.site._registry[Group], GroupAdmin)
