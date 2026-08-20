import shutil
import tempfile

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from accounts.models import User
from expenses.models import ExpenseReport, TravelDocument

MEDIA_ROOT = tempfile.mkdtemp(prefix="expense_reports_tests_")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ExpenseReportRulesTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.employee = User.objects.create_user(
            username="emp@example.com", email="emp@example.com", password="x", department="TI"
        )
        self.admin = User.objects.create_user(
            username="admin@example.com", email="admin@example.com", password="x", is_staff=True
        )
        self.report = ExpenseReport.objects.create(user=self.employee, title="Viaje a CDMX")

    def _add_document(self, amount="100.00"):
        return TravelDocument.objects.create(
            expense_report=self.report,
            file=SimpleUploadedFile("boleto.pdf", b"contenido", content_type="application/pdf"),
            type=TravelDocument.DocType.VUELO,
            amount=amount,
            document_date="2026-08-01",
        )

    def test_submit_without_documents_raises(self):
        with self.assertRaises(ValidationError):
            self.report.submit()
        self.assertEqual(self.report.status, ExpenseReport.Status.DRAFT)

    def test_submit_with_documents_moves_to_submitted(self):
        self._add_document()
        self.report.submit()
        self.assertEqual(self.report.status, ExpenseReport.Status.SUBMITTED)
        self.assertIsNotNone(self.report.submitted_at)

    def test_submit_when_not_draft_raises(self):
        self._add_document()
        self.report.submit()
        with self.assertRaises(ValidationError):
            self.report.submit()

    def test_approve_sets_reviewer_and_status(self):
        self._add_document()
        self.report.submit()

        self.report.approve(self.admin, "Todo en orden")

        self.assertEqual(self.report.status, ExpenseReport.Status.APPROVED)
        self.assertEqual(self.report.reviewed_by, self.admin)
        self.assertEqual(self.report.review_note, "Todo en orden")
        self.assertIsNotNone(self.report.reviewed_at)

    def test_approve_when_not_submitted_raises(self):
        with self.assertRaises(ValidationError):
            self.report.approve(self.admin, "")

    def test_reject_without_note_raises(self):
        self._add_document()
        self.report.submit()
        with self.assertRaises(ValidationError):
            self.report.reject(self.admin, "")

    def test_reject_with_note_sets_status(self):
        self._add_document()
        self.report.submit()

        self.report.reject(self.admin, "Faltan comprobantes")

        self.assertEqual(self.report.status, ExpenseReport.Status.REJECTED)
        self.assertEqual(self.report.review_note, "Faltan comprobantes")

    def test_total_amount_sums_all_documents(self):
        self._add_document("150.50")
        self._add_document("300.00")
        self.assertEqual(self.report.total_amount, 450.50)
