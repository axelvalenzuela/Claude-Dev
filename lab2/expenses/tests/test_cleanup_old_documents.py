"""expenses/management/commands/cleanup_old_documents.py — the file
retention policy (FILE_RETENTION_DAYS, expenses/policies.py)."""
import shutil
import tempfile
from datetime import timedelta
from io import StringIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import User
from expenses.models import ExpenseReport, ExpenseReportAuditLog, TravelDocument
from expenses.policies import FILE_RETENTION_DAYS

MEDIA_ROOT = tempfile.mkdtemp(prefix="expense_reports_tests_retention_")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class CleanupOldDocumentsTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="x", department="Sales"
        )
        self.report = ExpenseReport.objects.create(user=self.employee, title="Old trip")

        self.old_document = TravelDocument.objects.create(
            expense_report=self.report,
            file=SimpleUploadedFile("old.jpg", b"x", content_type="image/jpeg"),
            type=TravelDocument.DocType.TAXI,
            amount="20.00",
            document_date=timezone.now().date(),
        )
        old_cutoff = timezone.now() - timedelta(days=FILE_RETENTION_DAYS + 1)
        TravelDocument.objects.filter(pk=self.old_document.pk).update(uploaded_at=old_cutoff)

        self.recent_document = TravelDocument.objects.create(
            expense_report=self.report,
            file=SimpleUploadedFile("recent.jpg", b"x", content_type="image/jpeg"),
            type=TravelDocument.DocType.TAXI,
            amount="15.00",
            document_date=timezone.now().date(),
        )

    def test_deletes_files_older_than_the_retention_window(self):
        call_command("cleanup_old_documents", stdout=StringIO())

        self.old_document.refresh_from_db()
        self.recent_document.refresh_from_db()
        self.assertFalse(self.old_document.file)
        self.assertTrue(self.recent_document.file)

    def test_keeps_the_row_and_logs_an_audit_entry(self):
        call_command("cleanup_old_documents", stdout=StringIO())

        self.old_document.refresh_from_db()
        self.assertEqual(self.old_document.amount, 20.00)  # the row survives
        self.assertTrue(
            self.report.audit_log.filter(
                action=ExpenseReportAuditLog.Action.DOCUMENT_DELETED, note__icontains="retention"
            ).exists()
        )

    def test_dry_run_deletes_nothing(self):
        call_command("cleanup_old_documents", "--dry-run", stdout=StringIO())

        self.old_document.refresh_from_db()
        self.assertTrue(self.old_document.file)
