from datetime import date, timedelta
from decimal import Decimal
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from expenses.pdf_analysis import (
    MAX_PDF_PAGES,
    _guess_amount,
    _guess_currency,
    _guess_date,
    _guess_type,
    _guess_vendor,
    analyze_pdf,
    validate_pdf_page_count,
)
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


class GuessDateTests(SimpleTestCase):
    def test_detects_us_slash_date(self):
        self.assertEqual(_guess_date("Date: 08/15/2025"), date(2025, 8, 15))

    def test_detects_iso_date(self):
        self.assertEqual(_guess_date("Issued 2025-08-15"), date(2025, 8, 15))

    def test_ignores_a_future_date(self):
        # A misread digit producing a future date is worse than no date at
        # all — the field falls back to today's default instead.
        future = (date.today() + timedelta(days=30)).strftime("%m/%d/%Y")
        self.assertIsNone(_guess_date(f"Date: {future}"))

    def test_returns_none_when_no_date_found(self):
        self.assertIsNone(_guess_date("No dates on this line"))


class GuessVendorTests(SimpleTestCase):
    def test_picks_the_first_short_text_line(self):
        pages = ["United Airlines, INC\nBoarding Pass\nFlight AA123"]
        self.assertEqual(_guess_vendor(pages), "United Airlines, INC")

    def test_skips_a_line_that_is_mostly_a_price(self):
        pages = ["$85.50\nHotel Paradiso\nCheck-in Aug 1"]
        self.assertEqual(_guess_vendor(pages), "Hotel Paradiso")

    def test_returns_none_for_no_pages(self):
        self.assertIsNone(_guess_vendor([]))


class GuessCurrencyTests(SimpleTestCase):
    def test_detects_mxn(self):
        self.assertEqual(_guess_currency("Total: 500.00 MXN"), "MXN")

    def test_detects_usd(self):
        self.assertEqual(_guess_currency("Total: $50.00 USD"), "USD")

    def test_returns_none_when_unclear(self):
        self.assertIsNone(_guess_currency("Total: $50.00"))


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

    def test_prioritizes_the_first_two_pages(self):
        # The real charge (page 1) should win even though a much bigger,
        # unrelated number shows up later in the document (e.g. a loyalty
        # program balance on page 4).
        pdf_bytes = _make_pdf_bytes([
            "Hotel Reservation Total $85.50",
            "Continued booking details",
            "Rewards balance $9999.00",
            "Terms and conditions",
        ])

        result = analyze_pdf(BytesIO(pdf_bytes))

        self.assertEqual(result.extracted_amount, Decimal("85.50"))
        self.assertEqual(result.detected_type, "hotel")

    def test_extracts_date_vendor_and_currency_alongside_amount_and_type(self):
        pdf_bytes = _make_pdf_bytes(
            "Hotel Paradiso\nCheck-in 08/15/2025\nHotel Reservation Total $85.50 USD"
        )

        result = analyze_pdf(BytesIO(pdf_bytes))

        self.assertEqual(result.extracted_amount, Decimal("85.50"))
        self.assertEqual(result.detected_type, "hotel")
        self.assertEqual(result.extracted_date, date(2025, 8, 15))
        self.assertEqual(result.extracted_vendor, "Hotel Paradiso")
        self.assertEqual(result.detected_currency, "USD")

    def test_falls_back_to_later_pages_when_nothing_on_the_first_two(self):
        pdf_bytes = _make_pdf_bytes([
            "No relevant information here",
            "Still nothing useful",
            "Taxi fare receipt: driver Juan, ride fare $18.20",
        ])

        result = analyze_pdf(BytesIO(pdf_bytes))

        self.assertEqual(result.extracted_amount, Decimal("18.20"))
        self.assertEqual(result.detected_type, "taxi")


class ValidatePdfPageCountTests(SimpleTestCase):
    def test_allows_pdf_within_page_limit(self):
        pdf_bytes = _make_pdf_bytes(["Page 1", "Page 2", "Page 3", "Page 4"])
        file = SimpleUploadedFile("receipt.pdf", pdf_bytes, content_type="application/pdf")

        validate_pdf_page_count(file)  # should not raise

    def test_rejects_pdf_over_page_limit(self):
        pdf_bytes = _make_pdf_bytes(["Page 1", "Page 2", "Page 3", "Page 4", "Page 5"])
        file = SimpleUploadedFile("receipt.pdf", pdf_bytes, content_type="application/pdf")

        with self.assertRaises(ValidationError) as ctx:
            validate_pdf_page_count(file)
        self.assertIn(str(MAX_PDF_PAGES), str(ctx.exception))

    def test_ignores_non_pdf_files(self):
        file = SimpleUploadedFile("photo.jpg", b"fake-image", content_type="image/jpeg")

        validate_pdf_page_count(file)  # should not raise

    def test_ignores_unreadable_pdfs(self):
        file = SimpleUploadedFile("broken.pdf", b"not really a pdf", content_type="application/pdf")

        validate_pdf_page_count(file)  # fails open — should not raise
