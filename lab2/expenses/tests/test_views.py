import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.models import User
from expenses.models import ExpenseReport

MEDIA_ROOT = tempfile.mkdtemp(prefix="expense_reports_tests_")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ReportFlowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123", department="Ventas"
        )
        self.other_employee = User.objects.create_user(
            username="luis@example.com", email="luis@example.com", password="clave123", department="TI"
        )
        self.client.login(username="ana@example.com", password="clave123")

    def _create_report(self):
        response = self.client.post(
            reverse("reports:create"), {"title": "Viaje a CDMX", "description": "Cliente X"}
        )
        return ExpenseReport.objects.get(title="Viaje a CDMX", user=self.employee), response

    def test_create_report_belongs_to_current_user(self):
        report, response = self._create_report()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(report.user, self.employee)
        self.assertEqual(report.status, ExpenseReport.Status.DRAFT)

    def test_upload_document_then_submit(self):
        report, _ = self._create_report()

        upload_response = self.client.post(
            reverse("reports:upload_document", args=[report.pk]),
            {
                "type": "vuelo",
                "document_date": "2026-08-01",
                "amount": "1200.00",
                "file": SimpleUploadedFile("boleto.pdf", b"contenido", content_type="application/pdf"),
            },
        )
        self.assertEqual(upload_response.status_code, 302)
        self.assertEqual(report.documents.count(), 1)

        submit_response = self.client.post(reverse("reports:submit", args=[report.pk]))
        self.assertEqual(submit_response.status_code, 302)

        report.refresh_from_db()
        self.assertEqual(report.status, ExpenseReport.Status.SUBMITTED)

    def test_cannot_submit_without_documents(self):
        report, _ = self._create_report()

        self.client.post(reverse("reports:submit", args=[report.pk]))

        report.refresh_from_db()
        self.assertEqual(report.status, ExpenseReport.Status.DRAFT)

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
            username="ana@example.com", email="ana@example.com", password="clave123", department="Ventas"
        )
        self.admin = User.objects.create_superuser(
            username="admin@example.com", email="admin@example.com", password="clave123"
        )

        self.report = ExpenseReport.objects.create(user=self.employee, title="Viaje a CDMX")
        self.report.documents.create(
            file=SimpleUploadedFile("boleto.pdf", b"x", content_type="application/pdf"),
            type="vuelo",
            amount="1200.00",
            document_date="2026-08-01",
        )
        self.report.submit()
        self.report.save()

    def test_non_staff_user_cannot_reach_admin(self):
        self.client.login(username="ana@example.com", password="clave123")
        response = self.client.get(reverse("admin:expenses_expensereport_changelist"))
        self.assertEqual(response.status_code, 302)  # redirige a login del admin

    def _inline_management_data(self):
        # El inline de documentos es de solo lectura, pero el admin de Django
        # igual exige el formset management data (y el id de cada fila) en el POST.
        documents = list(self.report.documents.all())
        data = {
            "documents-TOTAL_FORMS": str(len(documents)),
            "documents-INITIAL_FORMS": str(len(documents)),
            "documents-MIN_NUM_FORMS": "0",
            "documents-MAX_NUM_FORMS": "1000",
        }
        for index, document in enumerate(documents):
            data[f"documents-{index}-id"] = str(document.pk)
        return data

    def test_admin_can_approve_report(self):
        self.client.login(username="admin@example.com", password="clave123")

        url = reverse("admin:expenses_expensereport_change", args=[self.report.pk])
        response = self.client.post(
            url,
            {
                "status": "approved",
                "review_note": "Todo en orden",
                "_save": "Save",
                **self._inline_management_data(),
            },
        )

        self.report.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.report.status, ExpenseReport.Status.APPROVED)
        self.assertEqual(self.report.reviewed_by, self.admin)
        self.assertEqual(self.report.review_note, "Todo en orden")

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
        self.assertEqual(response.status_code, 200)  # se queda en el form con el error
        self.assertEqual(self.report.status, ExpenseReport.Status.SUBMITTED)
