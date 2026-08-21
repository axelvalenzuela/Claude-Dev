"""OwnedReportMixin (expenses/views/mixins.py): an employee can never see or
act on another employee's report, not even by guessing its id."""
import shutil
import tempfile

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from expenses.models import ExpenseReport

MEDIA_ROOT = tempfile.mkdtemp(prefix="expense_reports_tests_access_")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ReportAccessTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123", department="Sales"
        )
        self.other_employee = User.objects.create_user(
            username="luis@example.com", email="luis@example.com", password="clave123", department="IT"
        )

    def test_employee_cannot_see_another_employees_report(self):
        report = ExpenseReport.objects.create(user=self.employee, title="Trip to Mexico City", supervisor_name="Maria Lopez")

        self.client.login(username="luis@example.com", password="clave123")
        response = self.client.get(reverse("reports:detail", args=[report.pk]))

        self.assertEqual(response.status_code, 404)
