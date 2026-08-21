"""Both notification context processors (accounts/context_processors.py):
the admin's "reports to review" banner and the employee's "your report was
approved/rejected" banner."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.context_processors import pending_reports_notification, recent_review_notification
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
        self.assertContains(response, "awaiting your review")


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
