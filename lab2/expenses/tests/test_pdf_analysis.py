from decimal import Decimal
from io import BytesIO

from django.test import SimpleTestCase

from expenses.pdf_analysis import _guess_amount, _guess_type, analyze_pdf
from expenses.tests.helpers import make_pdf_bytes as _make_pdf_bytes


class GuessAmountTests(SimpleTestCase):
    def test_picks_the_largest_amount_as_the_total(self):
        text = "Subtotal $40.00\nTax $5.50\nTotal $45.50"
        self.assertEqual(_guess_amount(text), Decimal("45.50"))

    def test_handles_thousands_separator(self):
        text = "Fare: $1,234.56"
        self.assertEqual(_guess_amount(text), Decimal("1234.56"))

    def test_returns_none_when_no_amount_found(self):
        self.assertIsNone(_guess_amount("No prices here"))


class GuessTypeTests(SimpleTestCase):
    def test_detects_flight(self):
        text = "Your Boarding Pass — Flight AA123, Gate 22, Departure 10:00"
        self.assertEqual(_guess_type(text), "flight")

    def test_detects_hotel(self):
        text = "Hotel Reservation Confirmation — Check-in Aug 1, Check-out Aug 3, nightly rate $150"
        self.assertEqual(_guess_type(text), "hotel")

    def test_detects_taxi(self):
        text = "Uber trip fare receipt — driver Juan, ride fare $18.20"
        self.assertEqual(_guess_type(text), "taxi")

    def test_detects_meal(self):
        text = "Restaurant receipt — dinner for 2, server: Maria"
        self.assertEqual(_guess_type(text), "meal")

    def test_returns_none_when_no_keywords_match(self):
        self.assertIsNone(_guess_type("Lorem ipsum dolor sit amet"))


class AnalyzePdfTests(SimpleTestCase):
    def test_extracts_amount_and_type_from_a_real_pdf(self):
        pdf_bytes = _make_pdf_bytes("Hotel Reservation Total $85.50")

        result = analyze_pdf(BytesIO(pdf_bytes))

        self.assertEqual(result.extracted_amount, Decimal("85.50"))
        self.assertEqual(result.detected_type, "hotel")

    def test_gracefully_handles_a_non_pdf_file(self):
        result = analyze_pdf(BytesIO(b"not a pdf at all"))

        self.assertIsNone(result.extracted_amount)
        self.assertIsNone(result.detected_type)
