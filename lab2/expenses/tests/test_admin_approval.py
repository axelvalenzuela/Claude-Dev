"""ExpenseReportAdmin (expenses/admin/reports.py): the approve/reject
change form, including the CEO-clause and rejection-note requirements, and
that a non-staff user can't reach the admin at all."""
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import User
from expenses.models import ExpenseReport, ExpenseReportAuditLog, TravelDocument

MEDIA_ROOT = tempfile.mkdtemp(prefix="expense_reports_tests_admin_approval_")
TODAY = timezone.now().date()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class AdminApprovalFlowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.employee = User.objects.create_user(
            username="ana@example.com",
            email="ana@example.com",
            password="clave123",
            first_name="Ana",
            last_name="Lopez",
            department="Sales",
            employee_number="1234567",
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

    def test_approving_deletes_originals_and_names_exports_per_rh_convention(self):
        self.client.login(username="admin@example.com", password="clave123")
        document = self.report.documents.first()

        url = reverse("admin:expenses_expensereport_change", args=[self.report.pk])
        self.client.post(
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
        document.refresh_from_db()

        self.assertTrue(self.report.excel_snapshot)
        self.assertTrue(self.report.word_snapshot)
        submitted_date = self.report.submitted_at.date().isoformat()
        expected_stem = f"Ana_Lopez_{submitted_date}_1234567_APROBADO"
        self.assertIn(expected_stem, self.report.excel_snapshot.name)
        self.assertIn(expected_stem, self.report.word_snapshot.name)

        # The original receipt is gone now that the report is approved.
        self.assertFalse(document.file)
        self.assertEqual(TravelDocument.objects.get(pk=document.pk).amount, document.amount)

    def test_rejecting_leaves_originals_and_exports_untouched(self):
        self.client.login(username="admin@example.com", password="clave123")
        document = self.report.documents.first()

        url = reverse("admin:expenses_expensereport_change", args=[self.report.pk])
        self.client.post(
            url,
            {
                "status": "rejected",
                "review_note": "Missing itemized receipt",
                "_save": "Save",
                **self._inline_management_data(),
            },
        )

        self.report.refresh_from_db()
        document.refresh_from_db()
        self.assertFalse(self.report.excel_snapshot)
        self.assertFalse(self.report.word_snapshot)
        self.assertTrue(document.file)

    def test_change_form_shows_download_history_button(self):
        # Repurposes the object-tools slot Django's default "History" link
        # used to occupy — see templates/admin/expenses/expensereport/
        # change_form_object_tools.html.
        self.client.login(username="admin@example.com", password="clave123")
        url = reverse("admin:expenses_expensereport_change", args=[self.report.pk])
        response = self.client.get(url)
        self.assertContains(response, "Download history")
        self.assertContains(
            response, reverse("admin:expenses_expensereport_download_history", args=[self.report.pk])
        )

    def test_download_history_includes_rejection_note(self):
        self.client.login(username="admin@example.com", password="clave123")
        url = reverse("admin:expenses_expensereport_change", args=[self.report.pk])
        self.client.post(
            url,
            {
                "status": "rejected",
                "review_note": "Missing itemized receipt",
                "_save": "Save",
                **self._inline_management_data(),
            },
        )

        history_url = reverse("admin:expenses_expensereport_download_history", args=[self.report.pk])
        response = self.client.get(history_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        from io import BytesIO

        from docx import Document

        document = Document(BytesIO(response.content))
        text = "\n".join(
            cell.text for table in document.tables for row in table.rows for cell in row.cells
        )
        self.assertIn("Rejected", text)
        self.assertIn("Missing itemized receipt", text)

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
