import shutil
import tempfile
from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from accounts.models import User
from expenses.models import ExpenseReport, TravelDocument
from expenses.policies import DAILY_LIMIT_USD, MAX_TRIP_SPAN_DAYS, validate_trip_span

MEDIA_ROOT = tempfile.mkdtemp(prefix="expense_reports_tests_")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ExpenseReportRulesTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.employee = User.objects.create_user(
            username="emp@example.com", email="emp@example.com", password="x", department="IT"
        )
        self.admin = User.objects.create_user(
            username="admin@example.com", email="admin@example.com", password="x", is_staff=True
        )
        self.report = ExpenseReport.objects.create(user=self.employee, title="Trip to Mexico City")

    def _add_document(self, amount="100.00", doc_type=TravelDocument.DocType.FLIGHT, date=None):
        return TravelDocument.objects.create(
            expense_report=self.report,
            file=SimpleUploadedFile("receipt.pdf", b"content", content_type="application/pdf"),
            type=doc_type,
            amount=amount,
            document_date=date or timezone.now().date(),
        )

    # --- submit() -------------------------------------------------------

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

    def test_submit_past_deadline_raises(self):
        old_flight_date = timezone.now().date() - timedelta(days=40)
        self._add_document(doc_type=TravelDocument.DocType.FLIGHT, date=old_flight_date)

        with self.assertRaises(ValidationError):
            self.report.submit()
        self.assertEqual(self.report.status, ExpenseReport.Status.DRAFT)

    def test_submit_within_deadline_succeeds(self):
        recent_flight_date = timezone.now().date() - timedelta(days=20)
        self._add_document(doc_type=TravelDocument.DocType.FLIGHT, date=recent_flight_date)

        self.report.submit()
        self.assertEqual(self.report.status, ExpenseReport.Status.SUBMITTED)

    # --- approve() / reject() -------------------------------------------

    def test_approve_requires_ceo_clause_ack(self):
        self._add_document()
        self.report.submit()

        with self.assertRaises(ValidationError):
            self.report.approve(self.admin, "Looks good", ceo_clause_ack=False)
        self.assertEqual(self.report.status, ExpenseReport.Status.SUBMITTED)

    def test_approve_with_ceo_clause_ack_sets_status_and_clause(self):
        self._add_document()
        self.report.submit()

        self.report.approve(self.admin, "Looks good", ceo_clause_ack=True)

        self.assertEqual(self.report.status, ExpenseReport.Status.APPROVED)
        self.assertEqual(self.report.reviewed_by, self.admin)
        self.assertTrue(self.report.ceo_authorized)
        self.assertIn("Steffan Widmer", self.report.approval_clause)

    def test_approve_when_not_submitted_raises(self):
        with self.assertRaises(ValidationError):
            self.report.approve(self.admin, "", ceo_clause_ack=True)

    def test_reject_without_note_raises(self):
        self._add_document()
        self.report.submit()
        with self.assertRaises(ValidationError):
            self.report.reject(self.admin, "")

    def test_reject_with_note_sets_status(self):
        self._add_document()
        self.report.submit()

        self.report.reject(self.admin, "Missing receipts")

        self.assertEqual(self.report.status, ExpenseReport.Status.REJECTED)
        self.assertEqual(self.report.review_note, "Missing receipts")

    # --- totals & policy --------------------------------------------------

    def test_total_amount_sums_all_documents(self):
        self._add_document("150.50")
        self._add_document("300.00")
        self.assertEqual(self.report.total_amount, Decimal("450.50"))

    def test_daily_totals_flags_days_over_limit(self):
        day = timezone.now().date()
        self._add_document("40.00", date=day)
        self._add_document("30.00", date=day)  # same day, total 70 > 60

        totals = self.report.daily_totals()

        self.assertEqual(len(totals), 1)
        self.assertEqual(totals[0]["total"], Decimal("70.00"))
        self.assertTrue(totals[0]["over_limit"])
        self.assertTrue(self.report.has_policy_violations)

    def test_daily_totals_within_limit_not_flagged(self):
        day = timezone.now().date()
        self._add_document("30.00", date=day)

        self.assertFalse(self.report.has_policy_violations)
        self.assertEqual(DAILY_LIMIT_USD, Decimal("60.00"))

    def test_trip_start_date_prefers_flight_document(self):
        self._add_document(doc_type=TravelDocument.DocType.HOTEL, date=timezone.now().date())
        flight_date = timezone.now().date() - timedelta(days=5)
        self._add_document(doc_type=TravelDocument.DocType.FLIGHT, date=flight_date)

        self.assertEqual(self.report.trip_start_date, flight_date)

    def test_trip_date_range_spans_earliest_to_latest_document(self):
        start = timezone.now().date() - timedelta(days=10)
        end = timezone.now().date()
        self._add_document(date=start)
        self._add_document(date=end)

        self.assertEqual(self.report.trip_date_range, (start, end))

    def test_trip_date_range_none_without_documents(self):
        self.assertIsNone(self.report.trip_date_range)


class ValidateTripSpanTests(TestCase):
    def test_allows_dates_within_the_span(self):
        base = timezone.now().date()
        dates = [base, base + timedelta(days=MAX_TRIP_SPAN_DAYS)]

        validate_trip_span(dates)  # should not raise

    def test_rejects_dates_further_apart_than_the_span(self):
        base = timezone.now().date()
        dates = [base, base + timedelta(days=MAX_TRIP_SPAN_DAYS + 1)]

        with self.assertRaises(ValidationError):
            validate_trip_span(dates)

    def test_march_and_june_receipts_are_rejected_together(self):
        march = timezone.now().date().replace(month=3, day=1)
        june = march.replace(month=6, day=1)

        with self.assertRaises(ValidationError):
            validate_trip_span([march, june])

    def test_single_date_or_empty_never_raises(self):
        validate_trip_span([])
        validate_trip_span([timezone.now().date()])
