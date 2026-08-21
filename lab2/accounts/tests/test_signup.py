"""Public self-service registration: creates a regular employee (never
staff), and every account gets a unique random employee number."""
from django.test import TestCase
from django.urls import reverse

from accounts.models import User, generate_employee_number


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
        self.assertIsNotNone(user.employee_number)
        self.assertEqual(len(user.employee_number), 7)
        self.assertTrue(user.employee_number.isdigit())

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


class EmployeeNumberTests(TestCase):
    def test_generate_employee_number_is_unique(self):
        User.objects.create_user(
            username="a@example.com", email="a@example.com", password="x", employee_number="1234567"
        )

        number = generate_employee_number()

        self.assertNotEqual(number, "1234567")
        self.assertEqual(len(number), 7)

    def test_two_signups_get_different_numbers(self):
        self.client.post(
            reverse("signup"),
            {
                "first_name": "Ana Perez",
                "department": "Sales",
                "email": "ana@example.com",
                "password1": "clave-super-segura-1",
                "password2": "clave-super-segura-1",
            },
        )
        self.client.logout()
        self.client.post(
            reverse("signup"),
            {
                "first_name": "Luis Gomez",
                "department": "IT",
                "email": "luis@example.com",
                "password1": "clave-super-segura-1",
                "password2": "clave-super-segura-1",
            },
        )

        ana = User.objects.get(email="ana@example.com")
        luis = User.objects.get(email="luis@example.com")
        self.assertNotEqual(ana.employee_number, luis.employee_number)
