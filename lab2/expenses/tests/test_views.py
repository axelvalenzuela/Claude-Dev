import shutil
import tempfile
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from expenses.models import ExpenseReport, ExpenseReportAuditLog

MEDIA_ROOT = tempfile.mkdtemp(prefix="expense_reports_tests_")
TODAY = timezone.now().date()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ReportFlowTests(TestCase):
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
        self.client.login(username="ana@example.com", password="clave123")

    def _create_report(self):
        response = self.client.post(
            reverse("reports:create"), {"title": "Trip to Mexico City", "description": "Client X"}
        )
        return ExpenseReport.objects.get(title="Trip to Mexico City", user=self.employee), response

    def test_create_report_belongs_to_current_user(self):
        report, response = self._create_report()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(report.user, self.employee)
        self.assertEqual(report.status, ExpenseReport.Status.DRAFT)

    def test_create_report_logs_audit_entry(self):
        report, _ = self._create_report()
        self.assertTrue(
            report.audit_log.filter(action=ExpenseReportAuditLog.Action.CREATED).exists()
        )

    def test_upload_document_then_submit(self):
        report, _ = self._create_report()

        upload_response = self.client.post(
            reverse("reports:upload_document", args=[report.pk]),
            {
                "type": "flight",
                "document_date": TODAY.isoformat(),
                "amount": "1200.00",
                "file": SimpleUploadedFile("boarding_pass.pdf", b"content", content_type="application/pdf"),
            },
        )
        self.assertEqual(upload_response.status_code, 302)
        self.assertEqual(report.documents.count(), 1)

        submit_response = self.client.post(reverse("reports:submit", args=[report.pk]))
        self.assertEqual(submit_response.status_code, 302)

        report.refresh_from_db()
        self.assertEqual(report.status, ExpenseReport.Status.SUBMITTED)
        self.assertTrue(
            report.audit_log.filter(action=ExpenseReportAuditLog.Action.SUBMITTED).exists()
        )

    def test_cannot_submit_without_documents(self):
        report, _ = self._create_report()

        self.client.post(reverse("reports:submit", args=[report.pk]))

        report.refresh_from_db()
        self.assertEqual(report.status, ExpenseReport.Status.DRAFT)

    def test_cannot_submit_past_deadline(self):
        report, _ = self._create_report()
        old_date = (TODAY - timedelta(days=45)).isoformat()

        self.client.post(
            reverse("reports:upload_document", args=[report.pk]),
            {
                "type": "flight",
                "document_date": old_date,
                "amount": "1200.00",
                "file": SimpleUploadedFile("boarding_pass.pdf", b"content", content_type="application/pdf"),
            },
        )

        response = self.client.post(reverse("reports:submit", args=[report.pk]), follow=True)

        report.refresh_from_db()
        self.assertEqual(report.status, ExpenseReport.Status.DRAFT)
        messages = [str(m) for m in response.context["messages"]]
        self.assertTrue(any("deadline" in m.lower() for m in messages))

    def test_employee_cannot_see_another_employees_report(self):
        report, _ = self._create_report()

        self.client.logout()
        self.client.login(username="luis@example.com", password="clave123")

        response = self.client.get(reverse("reports:detail", args=[report.pk]))
        self.assertEqual(response.status_code, 404)

    def test_export_excel_returns_xlsx(self):
        report, _ = self._create_report()

        response = self.client.get(reverse("reports:export_excel", args=[report.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )


ADMIN_MEDIA_ROOT = tempfile.mkdtemp(prefix="expense_reports_tests_admin_")


@override_settings(MEDIA_ROOT=ADMIN_MEDIA_ROOT)
class AdminApprovalFlowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(ADMIN_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123", department="Sales"
        )
        self.admin = User.objects.create_superuser(
            username="admin@example.com", email="admin@example.com", password="clave123"
        )

        self.report = ExpenseReport.objects.create(user=self.employee, title="Trip to Mexico City")
        self.report.documents.create(
            file=SimpleUploadedFile("boarding_pass.pdf", b"x", content_type="application/pdf"),
            type="flight",
            amount="1200.00",
            document_date=TODAY.isoformat(),
        )
        self.report.submit()
        self.report.save()

    def _inline_management_data(self):
        # The documents inline is read-only, but Django admin still requires
        # the formset management data (and each row's id) in the POST.
        documents = list(self.report.documents.all())
        data = {
            "documents-TOTAL_FORMS": str(len(documents)),
            "documents-INITIAL_FORMS": str(len(documents)),
            "documents-MIN_NUM_FORMS": "0",
            "documents-MAX_NUM_FORMS": "1000",
            "audit_log-TOTAL_FORMS": "0",
            "audit_log-INITIAL_FORMS": "0",
            "audit_log-MIN_NUM_FORMS": "0",
            "audit_log-MAX_NUM_FORMS": "0",
        }
        for index, document in enumerate(documents):
            data[f"documents-{index}-id"] = str(document.pk)
        return data

    def test_non_staff_user_cannot_reach_admin(self):
        self.client.login(username="ana@example.com", password="clave123")
        response = self.client.get(reverse("admin:expenses_expensereport_changelist"))
        self.assertEqual(response.status_code, 302)  # redirects to the admin login

    def test_admin_approve_requires_ceo_clause_checkbox(self):
        self.client.login(username="admin@example.com", password="clave123")

        url = reverse("admin:expenses_expensereport_change", args=[self.report.pk])
        response = self.client.post(
            url,
            {
                "status": "approved",
                "review_note": "Looks good",
                "_save": "Save",
                # ceo_clause_ack intentionally omitted
                **self._inline_management_data(),
            },
        )

        self.report.refresh_from_db()
        self.assertEqual(response.status_code, 200)  # form re-rendered with the error
        self.assertEqual(self.report.status, ExpenseReport.Status.SUBMITTED)

    def test_admin_can_approve_report_with_ceo_clause_ack(self):
        self.client.login(username="admin@example.com", password="clave123")

        url = reverse("admin:expenses_expensereport_change", args=[self.report.pk])
        response = self.client.post(
            url,
            {
                "status": "approved",
                "review_note": "Looks good",
                "ceo_clause_ack": "on",
                "_save": "Save",
                **self._inline_management_data(),
            },
        )

        self.report.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.report.status, ExpenseReport.Status.APPROVED)
        self.assertEqual(self.report.reviewed_by, self.admin)
        self.assertTrue(self.report.ceo_authorized)
        self.assertIn("Steffan Widmer", self.report.approval_clause)
        self.assertTrue(
            self.report.audit_log.filter(action=ExpenseReportAuditLog.Action.APPROVED).exists()
        )

    def test_admin_reject_requires_note(self):
        self.client.login(username="admin@example.com", password="clave123")

        url = reverse("admin:expenses_expensereport_change", args=[self.report.pk])
        response = self.client.post(
            url,
            {
                "status": "rejected",
                "review_note": "",
                "_save": "Save",
                **self._inline_management_data(),
            },
        )

        self.report.refresh_from_db()
        self.assertEqual(response.status_code, 200)  # form re-rendered with the error
        self.assertEqual(self.report.status, ExpenseReport.Status.SUBMITTED)
