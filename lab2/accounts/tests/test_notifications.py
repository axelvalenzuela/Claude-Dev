"""The Dashboard/notification context processors (accounts/
context_processors.py): the admin's "reports to review" banner, the
Dashboard's Approved reports table, and the employee's "your report was
approved/rejected" banner."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.context_processors import (
    approved_reports_table,
    pending_reports_notification,
    recent_review_notification,
)
from accounts.models import User
from expenses.models import ExpenseReport

TODAY = timezone.now().date()


def fake_request(user):
    """A minimal stand-in for HttpRequest — the context processors here
    only ever read `.user` off it."""
    request = type("FakeRequest", (), {})()
    request.user = user
    return request


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

    def test_department_admin_sees_only_their_own_count(self):
        context = pending_reports_notification(fake_request(self.adrian))
        self.assertEqual(context["pending_reports_count"], 1)
        self.assertEqual(context["pending_reports_scoped_to_department"], "ICS")

    def test_hr_admin_sees_the_total_unscoped(self):
        context = pending_reports_notification(fake_request(self.iris))
        self.assertEqual(context["pending_reports_count"], 1)
        self.assertIsNone(context["pending_reports_scoped_to_department"])

    def test_regular_employee_gets_no_notification_context(self):
        context = pending_reports_notification(fake_request(self.ics_employee))
        self.assertEqual(context, {})

    def test_admin_dashboard_shows_the_banner(self):
        self.client.login(username="adrian.heymes@mhp.com", password="Adrian#2026Local")
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "Pending (1)")
        self.assertContains(response, "ICS trip")


class ApprovedReportsTableTests(TestCase):
    def setUp(self):
        self.ics_employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="x", department="ICS"
        )
        self.finance_employee = User.objects.create_user(
            username="ben@example.com", email="ben@example.com", password="x", department="Finance"
        )
        self.adrian = User.objects.get(email="adrian.heymes@mhp.com")
        self.iris = User.objects.get(email="iris.cortez@mhp.com")

        self.ics_report = self._approved_report(self.ics_employee, "ICS trip")
        self.finance_report = self._approved_report(self.finance_employee, "Finance trip")

    def _approved_report(self, employee, title):
        report = ExpenseReport.objects.create(user=employee, title=title, supervisor_name="S")
        report.documents.create(
            file=SimpleUploadedFile("r.jpg", b"x", content_type="image/jpeg"),
            type="hotel",
            amount="50.00",
            document_date=TODAY.isoformat(),
        )
        report.submit()
        report.approve(self.iris, "Looks good", ceo_clause_ack=True)
        report.save()
        return report

    def test_department_admin_sees_only_their_own_department(self):
        context = approved_reports_table(fake_request(self.adrian))
        titles = [r.title for r in context["approved_reports_list"]]
        self.assertEqual(titles, ["ICS trip"])

    def test_hr_admin_sees_every_department(self):
        context = approved_reports_table(fake_request(self.iris))
        titles = {r.title for r in context["approved_reports_list"]}
        self.assertEqual(titles, {"ICS trip", "Finance trip"})

    def test_regular_employee_gets_no_table_context(self):
        context = approved_reports_table(fake_request(self.ics_employee))
        self.assertEqual(context, {})

    def test_dashboard_shows_pending_and_approved_subtabs(self):
        self.client.login(username="iris.cortez@mhp.com", password="Iris#2026Local")
        response = self.client.get(reverse("admin:index"))
        self.assertContains(response, "Approved (2)")
        self.assertContains(response, "Finance trip")


class RecentReviewNotificationTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123", department="ICS"
        )
        self.iris = User.objects.get(email="iris.cortez@mhp.com")

        self.report = ExpenseReport.objects.create(user=self.employee, title="My trip", supervisor_name="S")
        self.report.documents.create(
            file=SimpleUploadedFile("r.jpg", b"x", content_type="image/jpeg"),
            type="hotel",
            amount="50.00",
            document_date=TODAY.isoformat(),
        )
        self.report.submit()

    def test_rejected_report_shows_up_with_note(self):
        self.report.reject(self.iris, "Missing itemized receipt")
        self.report.save()

        self.client.login(username="ana@example.com", password="clave123")
        response = self.client.get(reverse("reports:list"))

        self.assertContains(response, "Missing itemized receipt")
        self.assertContains(response, "rejected")

    def test_approved_report_shows_up(self):
        self.report.approve(self.iris, "All good", ceo_clause_ack=True)
        self.report.save()

        self.client.login(username="ana@example.com", password="clave123")
        response = self.client.get(reverse("reports:list"))

        self.assertContains(response, "approved")

    def test_admin_gets_no_employee_style_notification(self):
        self.assertEqual(recent_review_notification(fake_request(self.iris)), {})
