"""ReportCreateView (expenses/views/reports.py): creating a report, with or
without receipts attached in the same step, and every validation that can
reject the whole thing before anything is saved."""
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
from expenses.policies import MAX_TRIP_SPAN_DAYS
from expenses.tests.helpers import make_pdf_bytes as _make_pdf_bytes

MEDIA_ROOT = tempfile.mkdtemp(prefix="expense_reports_tests_creation_")
TODAY = timezone.now().date()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ReportCreationTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123", department="Sales"
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

    def test_create_rejects_pdf_with_too_many_pages(self):
        pdf_bytes = _make_pdf_bytes(["Page 1", "Page 2", "Page 3", "Page 4", "Page 5"])
        response = self.client.post(
            reverse("reports:create"),
            {
                "title": "Too many pages",
                "description": "",
                "supervisor_name": "Maria Lopez",
                "supervisor_email": "",
                "action": "draft",
                "files": [SimpleUploadedFile("receipt.pdf", pdf_bytes, content_type="application/pdf")],
                "doc_type": ["hotel"],
                "doc_date": [TODAY.isoformat()],
                "doc_amount": ["50.00"],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(ExpenseReport.objects.filter(title="Too many pages").exists())

    def test_create_rejects_receipts_from_unrelated_trips(self):
        march_date = TODAY.replace(month=3, day=1) if TODAY.month != 3 else TODAY
        june_date = march_date.replace(month=6)

        response = self.client.post(
            reverse("reports:create"),
            {
                "title": "Two different trips",
                "description": "",
                "supervisor_name": "Maria Lopez",
                "supervisor_email": "",
                "action": "draft",
                "files": [
                    SimpleUploadedFile("march.jpg", b"fake-image", content_type="image/jpeg"),
                    SimpleUploadedFile("june.jpg", b"fake-image", content_type="image/jpeg"),
                ],
                "doc_type": ["hotel", "hotel"],
                "doc_date": [march_date.isoformat(), june_date.isoformat()],
                "doc_amount": ["50.00", "60.00"],
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(ExpenseReport.objects.filter(title="Two different trips").exists())

    def test_create_allows_receipts_within_the_same_trip(self):
        start = TODAY
        end = TODAY + timedelta(days=MAX_TRIP_SPAN_DAYS - 1)

        response = self.client.post(
            reverse("reports:create"),
            {
                "title": "One trip, spread out",
                "description": "",
                "supervisor_name": "Maria Lopez",
                "supervisor_email": "",
                "action": "draft",
                "files": [
                    SimpleUploadedFile("start.jpg", b"fake-image", content_type="image/jpeg"),
                    SimpleUploadedFile("end.jpg", b"fake-image", content_type="image/jpeg"),
                ],
                "doc_type": ["hotel", "hotel"],
                "doc_date": [start.isoformat(), end.isoformat()],
                "doc_amount": ["50.00", "60.00"],
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(ExpenseReport.objects.filter(title="One trip, spread out").exists())
