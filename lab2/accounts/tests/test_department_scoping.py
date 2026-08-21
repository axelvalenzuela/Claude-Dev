"""A department admin (Adrian/ICS) must only see ICS reports; the HR admin
(Iris) must see every department's reports — expenses/admin/reports.py's
get_queryset()."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from expenses.models import ExpenseReport

TODAY = timezone.now().date()


class DepartmentScopedApprovalTests(TestCase):
    def setUp(self):
        self.ics_employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="x", department="ICS"
        )
        self.sales_employee = User.objects.create_user(
            username="luis@example.com", email="luis@example.com", password="x", department="Sales"
        )
        self.adrian = User.objects.get(email="adrian.heymes@mhp.com")
        self.iris = User.objects.get(email="iris.cortez@mhp.com")

        self.ics_report = self._submitted_report(self.ics_employee, "ICS trip")
        self.sales_report = self._submitted_report(self.sales_employee, "Sales trip")

    def _submitted_report(self, user, title):
        report = ExpenseReport.objects.create(user=user, title=title, supervisor_name="Someone")
        report.documents.create(
            file=SimpleUploadedFile("receipt.jpg", b"fake-image", content_type="image/jpeg"),
            type="hotel",
            amount="50.00",
            document_date=TODAY.isoformat(),
        )
        report.submit()
        report.save()
        return report

    def test_ics_admin_only_sees_ics_reports(self):
        self.client.login(username="adrian.heymes@mhp.com", password="Adrian#2026Local")

        response = self.client.get(reverse("admin:expenses_expensereport_changelist"))

        self.assertContains(response, "ICS trip")
        self.assertNotContains(response, "Sales trip")

    def test_hr_admin_sees_every_department(self):
        self.client.login(username="iris.cortez@mhp.com", password="Iris#2026Local")

        response = self.client.get(reverse("admin:expenses_expensereport_changelist"))

        self.assertContains(response, "ICS trip")
        self.assertContains(response, "Sales trip")

    def test_ics_admin_cannot_open_a_sales_report_directly(self):
        self.client.login(username="adrian.heymes@mhp.com", password="Adrian#2026Local")

        url = reverse("admin:expenses_expensereport_change", args=[self.sales_report.pk])
        response = self.client.get(url)

        # Outside his queryset, so Django admin's own "object not found"
        # handling kicks in: a redirect away with an error message, not the
        # report's content (never a 200 showing another department's data).
        self.assertEqual(response.status_code, 302)
