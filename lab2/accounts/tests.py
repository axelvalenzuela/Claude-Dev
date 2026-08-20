from django.test import TestCase
from django.urls import reverse

from .models import LoginEvent, User


class SignUpTests(TestCase):
    def test_signup_creates_employee_not_staff(self):
        response = self.client.post(
            reverse("signup"),
            {
                "first_name": "Ana Perez",
                "department": "Sales",
                "email": "ana@example.com",
                "password1": "clave-super-segura-1",
                "password2": "clave-super-segura-1",
            },
        )
        self.assertEqual(response.status_code, 302)

        user = User.objects.get(email="ana@example.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.department, "Sales")

    def test_signup_rejects_duplicate_email(self):
        User.objects.create_user(username="ana@example.com", email="ana@example.com", password="x")

        response = self.client.post(
            reverse("signup"),
            {
                "first_name": "Another Ana",
                "department": "IT",
                "email": "ana@example.com",
                "password1": "clave-super-segura-1",
                "password2": "clave-super-segura-1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "already exists")

    def test_login_required_for_reports(self):
        response = self.client.get(reverse("reports:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)


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
