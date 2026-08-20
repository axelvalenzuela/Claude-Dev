from decimal import Decimal
from io import BytesIO

from django.test import SimpleTestCase

from expenses.pdf_analysis import _guess_amount, _guess_type, analyze_pdf


def _make_pdf_bytes(text: str) -> bytes:
    """Hand-rolled minimal single-page PDF with a text-showing operator, just
    enough for pypdf's text extraction (used instead of pulling in a full PDF
    writer dependency for a handful of tests)."""
    content = f"BT /F1 18 Tf 10 100 Td ({text}) Tj ET".encode()
    return b"""%%PDF-1.4
1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj
2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj
3 0 obj<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /MediaBox [0 0 400 200] /Contents 5 0 R >>endobj
4 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj
5 0 obj<< /Length %d >>
stream
%s
endstream
endobj
trailer<< /Size 6 /Root 1 0 R >>
startxref
0
%%%%EOF
""" % (len(content), content)


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
