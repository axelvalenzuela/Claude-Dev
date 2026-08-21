"""Adding documents to a draft (UploadDocumentView) and submitting it
(SubmitReportView) — including the deadline/trip-span guards. File
archival (services.finalize_approval) is triggered by admin approval, not
by submission — see test_admin_approval.py — so a submitted report's
original documents are expected to still be there."""
import shutil
import tempfile
from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from expenses.models import ExpenseReport, ExpenseReportAuditLog
from expenses.policies import MAX_TRIP_SPAN_DAYS

MEDIA_ROOT = tempfile.mkdtemp(prefix="expense_reports_tests_submission_")
TODAY = timezone.now().date()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ReportSubmissionTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123", department="Sales"
        )
        self.client.login(username="ana@example.com", password="clave123")

    def _create_report(self):
        response = self.client.post(
            reverse("reports:create"),
            {
                "title": "Trip to Mexico City",
                "description": "Client X",
                "supervisor_name": "Maria Lopez",
                "supervisor_email": "",
            },
        )
        return ExpenseReport.objects.get(title="Trip to Mexico City", user=self.employee), response

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

    def test_submitting_keeps_the_originals_until_approval(self):
        report, _ = self._create_report()
        self.client.post(
            reverse("reports:upload_document", args=[report.pk]),
            {
                "type": "flight",
                "document_date": TODAY.isoformat(),
                "amount": "1200.00",
                "file": SimpleUploadedFile("boarding_pass.pdf", b"content", content_type="application/pdf"),
            },
        )
        document = report.documents.first()

        self.client.post(reverse("reports:submit", args=[report.pk]))

        report.refresh_from_db()
        document.refresh_from_db()
        # No snapshot yet — that's only generated once an admin approves.
        self.assertFalse(report.excel_snapshot)
        self.assertFalse(report.word_snapshot)
        self.assertTrue(document.file)

        # The original is still on the server — downloading it still works.
        response = self.client.get(
            reverse("reports:download_document", args=[report.pk, document.pk])
        )
        self.assertEqual(response.status_code, 200)

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

    def test_upload_document_rejects_date_outside_existing_trip(self):
        report, _ = self._create_report()
        self.client.post(
            reverse("reports:upload_document", args=[report.pk]),
            {
                "type": "hotel",
                "document_date": TODAY.isoformat(),
                "amount": "50.00",
                "file": SimpleUploadedFile("hotel.jpg", b"fake-image", content_type="image/jpeg"),
            },
        )

        far_date = TODAY + timedelta(days=MAX_TRIP_SPAN_DAYS + 5)
        response = self.client.post(
            reverse("reports:upload_document", args=[report.pk]),
            {
                "type": "taxi",
                "document_date": far_date.isoformat(),
                "amount": "20.00",
                "file": SimpleUploadedFile("taxi.jpg", b"fake-image", content_type="image/jpeg"),
            },
            follow=True,
        )

        self.assertEqual(report.documents.count(), 1)
        messages = [str(m) for m in response.context["messages"]]
        self.assertTrue(any("trip" in m.lower() for m in messages))
