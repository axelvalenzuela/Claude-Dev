from decimal import Decimal
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from expenses.pdf_analysis import MAX_PDF_PAGES, _guess_amount, _guess_type, analyze_pdf, validate_pdf_page_count
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
