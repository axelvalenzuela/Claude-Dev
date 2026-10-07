"""Login by company employee number, not just email
(accounts/backends.py:EmployeeNumberOrEmailBackend) — including that the
account-lockout counter (accounts/security.py) stays unified for one
account regardless of which identifier a given attempt used."""
from django.test import TestCase
from django.urls import reverse

from accounts.models import LoginEvent, User
from accounts.security import LOCKOUT_THRESHOLD, is_account_locked


class EmployeeNumberLoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ana@example.com",
            email="ana@example.com",
            password="clave123",
            employee_number="1234567",
        )

    def test_employee_login_succeeds_with_employee_number(self):
        response = self.client.post(
            reverse("login"), {"username": "1234567", "password": "clave123"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user, self.user)

    def test_employee_login_still_works_with_email(self):
        response = self.client.post(
            reverse("login"), {"username": "ana@example.com", "password": "clave123"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_wrong_password_with_employee_number_fails(self):
        response = self.client.post(
            reverse("login"), {"username": "1234567", "password": "wrong"}
        )
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_unknown_employee_number_fails_without_error(self):
        response = self.client.post(
            reverse("login"), {"username": "9999999", "password": "clave123"}
        )
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_successful_login_via_employee_number_logs_canonical_email(self):
        self.client.post(reverse("login"), {"username": "1234567", "password": "clave123"})
        event = LoginEvent.objects.filter(success=True).latest("created_at")
        self.assertEqual(event.email_attempted, "ana@example.com")

    def test_admin_login_also_accepts_employee_number(self):
        admin = User.objects.create_superuser(
            username="admin@example.com",
            email="admin@example.com",
            password="clave123",
            employee_number="7654321",
        )
        response = self.client.post(
            reverse("admin:login"), {"username": "7654321", "password": "clave123"}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertEqual(response.wsgi_request.user, admin)


class LockoutUnifiedAcrossIdentifiersTests(TestCase):
    """A three-strikes count split across "typed the email this time,
    the employee number next time" would defeat the lockout entirely —
    these confirm both identifiers feed the same counter."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="ana@example.com",
            email="ana@example.com",
            password="clave123",
            employee_number="1234567",
        )

    def test_mixed_identifier_failures_still_lock_the_account(self):
        self.client.post(reverse("login"), {"username": "ana@example.com", "password": "wrong"})
        self.client.post(reverse("login"), {"username": "1234567", "password": "wrong"})
        self.client.post(reverse("login"), {"username": "ana@example.com", "password": "wrong"})

        self.assertTrue(is_account_locked("ana@example.com"))

        response = self.client.post(
            reverse("login"), {"username": "1234567", "password": "clave123"}
        )
        self.assertContains(response, "Too many failed login attempts")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_failed_attempts_by_employee_number_are_logged_under_the_email(self):
        self.client.post(reverse("login"), {"username": "1234567", "password": "wrong"})
        event = LoginEvent.objects.filter(success=False).latest("created_at")
        self.assertEqual(event.email_attempted, "ana@example.com")
