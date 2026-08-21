"""The approved-vs-rejected donut chart's data (accounts/context_processors.py:approval_chart)."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from accounts.context_processors import approval_chart
from accounts.models import User
from expenses.models import ExpenseReport

TODAY = timezone.now().date()


def fake_request(user):
    request = type("FakeRequest", (), {})()
    request.user = user
    return request


class ApprovalChartTests(TestCase):
    def setUp(self):
        self.ics_employee = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="x", department="ICS"
        )
        self.iris = User.objects.get(email="iris.cortez@mhp.com")

    def _reviewed(self, status):
        report = ExpenseReport.objects.create(user=self.ics_employee, title="T", supervisor_name="S")
        report.documents.create(
            file=SimpleUploadedFile("r.jpg", b"x", content_type="image/jpeg"),
            type="hotel",
            amount="50.00",
            document_date=TODAY.isoformat(),
        )
        report.submit()
        if status == ExpenseReport.Status.APPROVED:
            report.approve(self.iris, "ok", ceo_clause_ack=True)
        else:
            report.reject(self.iris, "no")
        report.save()

    def test_no_reviews_yet_gives_zero_total(self):
        context = approval_chart(fake_request(self.iris))
        self.assertEqual(context["approval_chart_total"], 0)
        self.assertEqual(context["approval_chart_approved_pct"], 0)

    def test_computes_correct_percentages(self):
        self._reviewed(ExpenseReport.Status.APPROVED)
        self._reviewed(ExpenseReport.Status.APPROVED)
        self._reviewed(ExpenseReport.Status.REJECTED)

        context = approval_chart(fake_request(self.iris))

        self.assertEqual(context["approval_chart_total"], 3)
        self.assertEqual(context["approval_chart_approved"], 2)
        self.assertEqual(context["approval_chart_rejected"], 1)
        self.assertEqual(context["approval_chart_approved_pct"], 67)
