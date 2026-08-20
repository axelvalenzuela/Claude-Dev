from django.test import TestCase
from django.urls import reverse

from .models import User


class SignUpTests(TestCase):
    def test_signup_creates_employee_not_staff(self):
        response = self.client.post(
            reverse("signup"),
            {
                "first_name": "Ana Pérez",
                "department": "Ventas",
                "email": "ana@example.com",
                "password1": "clave-super-segura-1",
                "password2": "clave-super-segura-1",
            },
        )
        self.assertEqual(response.status_code, 302)

        user = User.objects.get(email="ana@example.com")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(user.department, "Ventas")

    def test_signup_rejects_duplicate_email(self):
        User.objects.create_user(username="ana@example.com", email="ana@example.com", password="x")

        response = self.client.post(
            reverse("signup"),
            {
                "first_name": "Otra Ana",
                "department": "TI",
                "email": "ana@example.com",
                "password1": "clave-super-segura-1",
                "password2": "clave-super-segura-1",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe una cuenta con ese correo")

    def test_login_required_for_reports(self):
        response = self.client.get(reverse("reports:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)
