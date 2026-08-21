"""ExportExcelView / ExportWordView (expenses/views/exports.py): a
still-draft report generates a preview on the fly; a submitted one serves
the permanent snapshot saved by services.finalize_submission."""
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from expenses.models import ExpenseReport

MEDIA_ROOT = tempfile.mkdtemp(prefix="expense_reports_tests_exports_")
TODAY = timezone.now().date()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ExportTests(TestCase):
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

    def test_export_excel_returns_xlsx(self):
        report, _ = self._create_report()

        response = self.client.get(reverse("reports:export_excel", args=[report.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def test_export_word_serves_the_saved_snapshot_after_submission(self):
        report, _ = self._create_report()
        self.client.post(
            reverse("reports:upload_document", args=[report.pk]),
            {
                "type": "hotel",
                "document_date": TODAY.isoformat(),
                "amount": "150.00",
                "file": SimpleUploadedFile("hotel.jpg", b"fake-image", content_type="image/jpeg"),
            },
        )
        self.client.post(reverse("reports:submit", args=[report.pk]))

        response = self.client.get(reverse("reports:export_word", args=[report.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    def test_export_word_for_a_draft_generates_on_the_fly(self):
        report, _ = self._create_report()  # still a draft, no snapshot saved yet

        response = self.client.get(reverse("reports:export_word", args=[report.pk]))

        self.assertEqual(response.status_code, 200)
