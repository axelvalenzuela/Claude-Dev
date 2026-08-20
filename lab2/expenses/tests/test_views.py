import shutil
import tempfile
from datetime import timedelta
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from expenses.models import ExpenseReport, ExpenseReportAuditLog
from expenses.tests.helpers import make_pdf_bytes as _make_pdf_bytes

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

    def _create_report(self, **extra):
        data = {
            "title": "Trip to Mexico City",
            "description": "Client X",
            "supervisor_name": "Maria Lopez",
            "supervisor_email": "",
        }
        data.update(extra)
        response = self.client.post(reverse("reports:create"), data)
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

    def test_create_requires_supervisor_name(self):
        response = self.client.post(
            reverse("reports:create"),
            {"title": "No supervisor", "description": "", "supervisor_name": "", "supervisor_email": ""},
        )
        self.assertEqual(response.status_code, 200)  # re-renders the form with an error
        self.assertFalse(ExpenseReport.objects.filter(title="No supervisor").exists())

    def test_create_with_attached_receipts_saves_documents(self):
        response = self.client.post(
            reverse("reports:create"),
            {
                "title": "Trip with receipts",
                "description": "",
                "supervisor_name": "Maria Lopez",
                "supervisor_email": "maria@example.com",
                "action": "draft",
                "files": [
                    SimpleUploadedFile("hotel.jpg", b"fake-image", content_type="image/jpeg"),
                ],
                "doc_type": ["hotel"],
                "doc_date": [TODAY.isoformat()],
                "doc_amount": ["150.00"],
            },
        )

        report = ExpenseReport.objects.get(title="Trip with receipts")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(report.documents.count(), 1)
        self.assertEqual(report.documents.first().amount, Decimal("150.00"))
        self.assertEqual(report.supervisor_name, "Maria Lopez")
        self.assertTrue(
            report.audit_log.filter(action=ExpenseReportAuditLog.Action.DOCUMENT_UPLOADED).exists()
        )

    def test_create_and_submit_in_one_step(self):
        response = self.client.post(
            reverse("reports:create"),
            {
                "title": "Trip create and submit",
                "description": "",
                "supervisor_name": "Maria Lopez",
                "supervisor_email": "",
                "action": "submit",
                "files": [
                    SimpleUploadedFile("hotel.jpg", b"fake-image", content_type="image/jpeg"),
                ],
                "doc_type": ["hotel"],
                "doc_date": [TODAY.isoformat()],
                "doc_amount": ["150.00"],
            },
        )

        report = ExpenseReport.objects.get(title="Trip create and submit")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(report.status, ExpenseReport.Status.SUBMITTED)

    def test_create_with_invalid_document_does_not_create_report(self):
        response = self.client.post(
            reverse("reports:create"),
            {
                "title": "Bad document",
                "description": "",
                "supervisor_name": "Maria Lopez",
                "supervisor_email": "",
                "action": "draft",
                "files": [
                    SimpleUploadedFile("hotel.jpg", b"fake-image", content_type="image/jpeg"),
                ],
                "doc_type": ["hotel"],
                "doc_date": [TODAY.isoformat()],
                "doc_amount": ["not-a-number"],
            },
        )

        self.assertEqual(response.status_code, 200)  # re-renders the form with the error
        self.assertFalse(ExpenseReport.objects.filter(title="Bad document").exists())

    def test_preview_document_extracts_amount_and_type_from_pdf(self):
        pdf_bytes = _make_pdf_bytes("Hotel Reservation Total $85.50")
        response = self.client.post(
            reverse("reports:preview_document"),
            {"file": SimpleUploadedFile("receipt.pdf", pdf_bytes, content_type="application/pdf")},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_pdf"])
        self.assertEqual(data["extracted_amount"], "85.50")
        self.assertEqual(data["detected_type"], "hotel")

    def test_preview_document_skips_non_pdf_files(self):
        response = self.client.post(
            reverse("reports:preview_document"),
            {"file": SimpleUploadedFile("photo.jpg", b"fake-image", content_type="image/jpeg")},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["is_pdf"])
        self.assertIsNone(data["extracted_amount"])


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
