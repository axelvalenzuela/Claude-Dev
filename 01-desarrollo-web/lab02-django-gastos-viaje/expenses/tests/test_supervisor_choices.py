"""The new-report form's supervisor dropdown (expenses/views/reports.py:
_supervisor_choices()) — populated from the real admin roster, each
option carrying the data-email the client-side script uses to fill in
the read-only email field."""
import re

from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class SupervisorChoicesTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123", department="Sales"
        )
        self.client.login(username="ana@example.com", password="clave123")

    def test_every_active_admin_appears_as_an_option(self):
        response = self.client.get(reverse("reports:create"))
        body = response.content.decode()

        for admin_email in [
            "iris.cortez@mhp.com",
            "adrian.heymes@mhp.com",
            "karen.plascencia@mhp.com",
            "steffan.widmer@mhp.com",
        ]:
            admin = User.objects.get(email=admin_email)
            self.assertIn(f'data-email="{admin.email}"', body)
            self.assertIn(admin.get_full_name(), body)

    def test_a_regular_employee_is_not_offered_as_a_supervisor(self):
        response = self.client.get(reverse("reports:create"))
        self.assertNotContains(response, f'data-email="{self.employee.email}"')

    def test_an_inactive_admin_is_excluded(self):
        admin = User.objects.get(email="iris.cortez@mhp.com")
        admin.is_active = False
        admin.save()

        response = self.client.get(reverse("reports:create"))
        self.assertNotContains(response, 'data-email="iris.cortez@mhp.com"')

    def test_supervisor_email_field_is_read_only(self):
        response = self.client.get(reverse("reports:create"))
        self.assertContains(response, 'id="id_supervisor_email"')
        self.assertContains(response, "readonly")

    def test_previously_selected_supervisor_stays_selected_after_a_validation_error(self):
        # Missing title -> the form re-renders invalid; the supervisor
        # picked before submitting shouldn't be lost.
        response = self.client.post(
            reverse("reports:create"),
            {
                "title": "",
                "description": "",
                "supervisor_name": "Iris Cortez",
                "supervisor_email": "iris.cortez@mhp.com",
                "action": "draft",
            },
        )
        self.assertEqual(response.status_code, 200)
        body = response.content.decode()

        # Find the <option> for Iris Cortez specifically and confirm it
        # (not some other option) is the one marked selected.
        match = re.search(r'<option value="Iris Cortez"[^>]*>', body)
        self.assertIsNotNone(match, "Expected an <option> for Iris Cortez")
        self.assertIn("selected", match.group(0))
