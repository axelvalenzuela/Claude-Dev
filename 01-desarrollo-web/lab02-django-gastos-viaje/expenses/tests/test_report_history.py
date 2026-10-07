"""ReportHistoryView (expenses/views/reports.py): the employee's
alphabetically-sorted archive of everything ever sent."""
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from expenses.models import ExpenseReport

MEDIA_ROOT = tempfile.mkdtemp(prefix="expense_reports_tests_history_")
TODAY = timezone.now().date()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ReportHistoryTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123", department="Sales"
        )
        self.client.login(username="ana@example.com", password="clave123")

    def _report(self, title, status=ExpenseReport.Status.DRAFT):
        report = ExpenseReport.objects.create(user=self.employee, title=title, supervisor_name="Someone")
        if status != ExpenseReport.Status.DRAFT:
            report.documents.create(
                file=SimpleUploadedFile("r.jpg", b"x", content_type="image/jpeg"),
                type="hotel",
                amount="10.00",
                document_date=TODAY.isoformat(),
            )
            report.submit()
            report.status = status
            report.save()
        return report

    def test_history_excludes_drafts(self):
        self._report("Zebra trip", status=ExpenseReport.Status.SUBMITTED)
        self._report("Draft trip")  # stays a draft

        response = self.client.get(reverse("reports:history"))

        titles = [r.title for r in response.context["reports"]]
        self.assertEqual(titles, ["Zebra trip"])

    def test_history_is_sorted_alphabetically(self):
        self._report("Zebra trip", status=ExpenseReport.Status.SUBMITTED)
        self._report("Alpha trip", status=ExpenseReport.Status.APPROVED)
        self._report("Mid trip", status=ExpenseReport.Status.REJECTED)

        response = self.client.get(reverse("reports:history"))

        titles = [r.title for r in response.context["reports"]]
        self.assertEqual(titles, ["Alpha trip", "Mid trip", "Zebra trip"])

    def test_history_shows_rejection_note(self):
        report = self._report("Rejected trip", status=ExpenseReport.Status.SUBMITTED)
        report.reject(self.employee, "Missing itemized receipt")
        report.save()

        response = self.client.get(reverse("reports:history"))

        self.assertContains(response, "Missing itemized receipt")
