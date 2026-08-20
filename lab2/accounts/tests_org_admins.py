"""Tests for the org-chart admin seeding, department-scoped visibility, and
the "reports to review" notification banner."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.context_processors import pending_reports_notification
from expenses.models import ExpenseReport
from .models import User

TODAY = timezone.now().date()


class OrgAdminSeedTests(TestCase):
    """The migration that seeds Iris Cortez (HR) and Adrian Heymes (ICS)
    already ran for the test database (migrations always run), so we can
    assert on its result directly."""

    def test_hr_admin_is_a_superuser_with_no_department_scope(self):
        iris = User.objects.get(email="iris.cortez@mhp.com")
        self.assertTrue(iris.is_staff)
        self.assertTrue(iris.is_superuser)
        self.assertEqual(iris.supervised_department, "")
        self.assertIsNotNone(iris.employee_number)

    def test_ics_admin_is_scoped_to_ics_only(self):
        adrian = User.objects.get(email="adrian.heymes@mhp.com")
        self.assertTrue(adrian.is_staff)
        self.assertFalse(adrian.is_superuser)
        self.assertEqual(adrian.supervised_department, "ICS")
        self.assertIsNotNone(adrian.employee_number)

    def test_org_admins_get_distinct_employee_numbers(self):
        iris = User.objects.get(email="iris.cortez@mhp.com")
        adrian = User.objects.get(email="adrian.heymes@mhp.com")
        self.assertNotEqual(iris.employee_number, adrian.employee_number)


class DepartmentScopedApprovalTests(TestCase):
    """A department admin (Adrian/ICS) must only see ICS reports; the HR
    admin (Iris) must see every department's reports."""

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
        report = ExpenseReport.objects.create(
            user=user, title=title, supervisor_name="Someone"
        )
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


class PendingReportsNotificationTests(TestCase):
    def setUp(self):
        self.ics_employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="x", department="ICS"
        )
        self.adrian = User.objects.get(email="adrian.heymes@mhp.com")
        self.iris = User.objects.get(email="iris.cortez@mhp.com")

        report = ExpenseReport.objects.create(user=self.ics_employee, title="ICS trip", supervisor_name="Adrian")
        report.documents.create(
            file=SimpleUploadedFile("receipt.jpg", b"fake-image", content_type="image/jpeg"),
            type="hotel",
            amount="50.00",
            document_date=TODAY.isoformat(),
        )
        report.submit()
        report.save()

    def _request_for(self, user):
        request = type("Req", (), {})()
        request.user = user
        return request

    def test_department_admin_sees_only_their_own_count(self):
        context = pending_reports_notification(self._request_for(self.adrian))
        self.assertEqual(context["pending_reports_count"], 1)
        self.assertEqual(context["pending_reports_scoped_to_department"], "ICS")

    def test_hr_admin_sees_the_total_unscoped(self):
        context = pending_reports_notification(self._request_for(self.iris))
        self.assertEqual(context["pending_reports_count"], 1)
        self.assertIsNone(context["pending_reports_scoped_to_department"])

    def test_regular_employee_gets_no_notification_context(self):
        context = pending_reports_notification(self._request_for(self.ics_employee))
        self.assertEqual(context, {})

    def test_admin_dashboard_shows_the_banner(self):
        self.client.login(username="adrian.heymes@mhp.com", password="Adrian#2026Local")
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "awaiting your review")
