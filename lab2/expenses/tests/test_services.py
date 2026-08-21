import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from accounts.models import User
from expenses.models import ExpenseReport, ExpenseReportAuditLog, TravelDocument
from expenses.services import finalize_approval

MEDIA_ROOT = tempfile.mkdtemp(prefix="expense_reports_tests_")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class FinalizeApprovalTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.employee = User.objects.create_user(
            username="ana@example.com",
            email="ana@example.com",
            password="x",
            first_name="Ana",
            last_name="Lopez",
            department="Sales",
            employee_number="1234567",
        )
        self.admin = User.objects.create_superuser(
            username="admin@example.com", email="admin@example.com", password="x"
        )
        self.report = ExpenseReport.objects.create(
            user=self.employee, title="Trip to Mexico City", supervisor_name="Maria Lopez"
        )
        self.document = TravelDocument.objects.create(
            expense_report=self.report,
            file=SimpleUploadedFile("hotel.jpg", b"fake-image", content_type="image/jpeg"),
            type=TravelDocument.DocType.HOTEL,
            amount="150.00",
            document_date="2026-08-01",
        )
        self.report.submit()
        self.report.save()
        self.report.approve(self.admin, "Looks good", ceo_clause_ack=True)
        self.report.save()

    def test_generates_and_saves_both_snapshots(self):
        finalize_approval(self.report, self.admin)

        self.report.refresh_from_db()
        self.assertTrue(self.report.excel_snapshot)
        self.assertTrue(self.report.word_snapshot)
        self.assertTrue(self.report.excel_snapshot.name.endswith(".xlsx"))
        self.assertTrue(self.report.word_snapshot.name.endswith(".docx"))

    def test_snapshots_are_named_per_rh_convention(self):
        finalize_approval(self.report, self.admin)

        self.report.refresh_from_db()
        submitted_date = self.report.submitted_at.date().isoformat()
        expected_stem = f"Ana_Lopez_{submitted_date}_1234567_APROBADO"
        self.assertIn(expected_stem, self.report.excel_snapshot.name)
        self.assertIn(expected_stem, self.report.word_snapshot.name)

    def test_removes_the_original_file_but_keeps_the_document_row(self):
        original_path = self.document.file.path

        finalize_approval(self.report, self.admin)

        self.document.refresh_from_db()
        self.assertFalse(self.document.file)  # the FieldFile is now empty
        self.assertEqual(self.document.amount, 150.00)  # the row itself survives
        self.assertEqual(self.document.file_name, "hotel.jpg")  # original name remembered
        self.assertFalse(__import__("os").path.exists(original_path))

    def test_logs_an_audit_entry(self):
        finalize_approval(self.report, self.admin)

        self.assertTrue(
            self.report.audit_log.filter(
                action=ExpenseReportAuditLog.Action.DOCUMENT_DELETED, note__icontains="approval"
            ).exists()
        )

    def test_daily_totals_still_work_after_files_are_removed(self):
        finalize_approval(self.report, self.admin)

        totals = self.report.daily_totals()
        self.assertEqual(len(totals), 1)
        self.assertEqual(totals[0]["total"], 150.00)
