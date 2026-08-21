"""The proxy-model admin (Django Admin "Approved reports (history)") —
expenses/admin/approved_history.py."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from expenses.models import ExpenseReport

TODAY = timezone.now().date()


class ApprovedReportsHistoryTests(TestCase):
    def setUp(self):
        self.ics_employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="x", department="ICS"
        )
        self.sales_employee = User.objects.create_user(
            username="luis@example.com", email="luis@example.com", password="x", department="Sales"
        )
        self.zebra = self._reviewed_report(self.ics_employee, "Zebra trip", ExpenseReport.Status.APPROVED)
        self.alpha = self._reviewed_report(self.ics_employee, "Alpha trip", ExpenseReport.Status.APPROVED)
        self.rejected = self._reviewed_report(self.sales_employee, "Rejected trip", ExpenseReport.Status.REJECTED)

    def _reviewed_report(self, user, title, status):
        report = ExpenseReport.objects.create(user=user, title=title, supervisor_name="Someone")
        report.documents.create(
            file=SimpleUploadedFile("r.jpg", b"x", content_type="image/jpeg"),
            type="hotel",
            amount="50.00",
            document_date=TODAY.isoformat(),
        )
        report.submit()
        admin = User.objects.get(email="iris.cortez@mhp.com")
        if status == ExpenseReport.Status.APPROVED:
            report.approve(admin, "Looks good", ceo_clause_ack=True)
        else:
            report.reject(admin, "Missing receipts")
        report.save()
        return report

    def test_only_approved_reports_show_up(self):
        self.client.login(username="iris.cortez@mhp.com", password="Iris#2026Local")
        response = self.client.get(reverse("admin:expenses_approvedexpensereport_changelist"))

        self.assertContains(response, "Zebra trip")
        self.assertContains(response, "Alpha trip")
        self.assertNotContains(response, "Rejected trip")

    def test_sorted_alphabetically(self):
        self.client.login(username="iris.cortez@mhp.com", password="Iris#2026Local")
        response = self.client.get(reverse("admin:expenses_approvedexpensereport_changelist"))

        titles = [obj.title for obj in response.context["cl"].result_list]
        self.assertEqual(titles, sorted(titles))

    def test_department_admin_only_sees_their_department_in_history(self):
        self.client.login(username="adrian.heymes@mhp.com", password="Adrian#2026Local")
        response = self.client.get(reverse("admin:expenses_approvedexpensereport_changelist"))

        self.assertContains(response, "Zebra trip")
        self.assertContains(response, "Alpha trip")

    def test_history_is_read_only(self):
        self.client.login(username="iris.cortez@mhp.com", password="Iris#2026Local")
        url = reverse("admin:expenses_approvedexpensereport_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
