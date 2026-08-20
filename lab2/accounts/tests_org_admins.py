"""Tests for the org-chart admin seeding, department-scoped visibility, and
the "reports to review" notification banner."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from accounts.context_processors import approval_chart, pending_reports_notification, recent_review_notification
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


class ApprovedReportsHistoryTests(TestCase):
    """The proxy-model admin (Django Admin "Approved reports (history)")."""

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


class ApprovalChartTests(TestCase):
    def setUp(self):
        self.ics_employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="x", department="ICS"
        )
        self.adrian = User.objects.get(email="adrian.heymes@mhp.com")
        self.iris = User.objects.get(email="iris.cortez@mhp.com")

    def _request_for(self, user):
        request = type("Req", (), {})()
        request.user = user
        return request

    def _reviewed(self, status):
        report = ExpenseReport.objects.create(user=self.ics_employee, title="T", supervisor_name="S")
        report.documents.create(
            file=SimpleUploadedFile("r.jpg", b"x", content_type="image/jpeg"),
            type="hotel",
            amount="50.00",
            document_date=TODAY.isoformat(),
        )
        report.submit()
        if status == ExpenseReport.Status.APPROVED:
            report.approve(self.iris, "ok", ceo_clause_ack=True)
        else:
            report.reject(self.iris, "no")
        report.save()

    def test_no_reviews_yet_gives_zero_total(self):
        context = approval_chart(self._request_for(self.iris))
        self.assertEqual(context["approval_chart_total"], 0)
        self.assertEqual(context["approval_chart_approved_pct"], 0)

    def test_computes_correct_percentages(self):
        self._reviewed(ExpenseReport.Status.APPROVED)
        self._reviewed(ExpenseReport.Status.APPROVED)
        self._reviewed(ExpenseReport.Status.REJECTED)

        context = approval_chart(self._request_for(self.iris))

        self.assertEqual(context["approval_chart_total"], 3)
        self.assertEqual(context["approval_chart_approved"], 2)
        self.assertEqual(context["approval_chart_rejected"], 1)
        self.assertEqual(context["approval_chart_approved_pct"], 67)


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
        request = type("Req", (), {})()
        request.user = self.iris
        self.assertEqual(recent_review_notification(request), {})
