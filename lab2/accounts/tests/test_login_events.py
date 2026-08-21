"""LoginEvent recording (accounts/signals.py) — the base audit trail that
accounts/security.py's lockout and the admin's traceability view both build
on top of."""
from django.test import TestCase
from django.urls import reverse

from accounts.models import LoginEvent, User


class LoginEventTraceabilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123"
        )

    def test_successful_login_is_recorded(self):
        self.client.post(reverse("login"), {"username": "ana@example.com", "password": "clave123"})

        event = LoginEvent.objects.get(email_attempted="ana@example.com", success=True)
        self.assertEqual(event.user, self.user)

    def test_failed_login_is_recorded_without_a_user(self):
        self.client.post(reverse("login"), {"username": "ana@example.com", "password": "wrong-password"})

        event = LoginEvent.objects.get(email_attempted="ana@example.com", success=False)
        self.assertIsNone(event.user)
