"""PreviewDocumentView (expenses/views/documents.py): the AJAX endpoint
that analyzes an attached file live, before anything is saved — a PDF's
text (pdf_analysis) or a photo's legibility (image_analysis)."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from expenses.tests.helpers import make_image_bytes as _make_image_bytes
from expenses.tests.helpers import make_pdf_bytes as _make_pdf_bytes


class PreviewDocumentTests(TestCase):
    def setUp(self):
        User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123", department="Sales"
        )
        self.client.login(username="ana@example.com", password="clave123")

    def test_preview_document_extracts_amount_and_type_from_pdf(self):
        pdf_bytes = _make_pdf_bytes("Hotel Reservation Total $85.50")
        response = self.client.post(
            reverse("reports:preview_document"),
            {"file": SimpleUploadedFile("receipt.pdf", pdf_bytes, content_type="application/pdf")},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_pdf"])
        self.assertEqual(data["extracted_amount"], "85.50")
        self.assertEqual(data["detected_type"], "hotel")

    def test_preview_document_also_extracts_date_vendor_and_currency(self):
        pdf_bytes = _make_pdf_bytes(
            "Hotel Paradiso\nCheck-in 08/15/2025\nHotel Reservation Total $85.50 USD"
        )
        response = self.client.post(
            reverse("reports:preview_document"),
            {"file": SimpleUploadedFile("receipt.pdf", pdf_bytes, content_type="application/pdf")},
        )

        data = response.json()
        self.assertEqual(data["extracted_date"], "2025-08-15")
        self.assertEqual(data["extracted_vendor"], "Hotel Paradiso")
        self.assertEqual(data["detected_currency"], "USD")

    def test_preview_document_reports_a_sharp_photo_as_readable_and_not_blurry(self):
        response = self.client.post(
            reverse("reports:preview_document"),
            {"file": SimpleUploadedFile("photo.jpg", _make_image_bytes(), content_type="image/jpeg")},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["is_pdf"])
        self.assertTrue(data["is_image"])
        self.assertTrue(data["image_is_readable"])
        self.assertFalse(data["image_is_blurry"])
        self.assertIsNone(data["extracted_amount"])  # never OCR'd — see image_analysis.py

    def test_preview_document_flags_a_blurry_photo(self):
        response = self.client.post(
            reverse("reports:preview_document"),
            {"file": SimpleUploadedFile("photo.jpg", _make_image_bytes(blur_radius=8), content_type="image/jpeg")},
        )

        data = response.json()
        self.assertTrue(data["image_is_readable"])
        self.assertTrue(data["image_is_blurry"])

    def test_preview_document_flags_an_unreadable_photo(self):
        response = self.client.post(
            reverse("reports:preview_document"),
            {"file": SimpleUploadedFile("photo.jpg", b"not really an image", content_type="image/jpeg")},
        )

        data = response.json()
        self.assertTrue(data["is_image"])
        self.assertFalse(data["image_is_readable"])

    def test_preview_document_skips_unrecognized_file_types(self):
        response = self.client.post(
            reverse("reports:preview_document"),
            {"file": SimpleUploadedFile("notes.txt", b"just some text", content_type="text/plain")},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["is_pdf"])
        self.assertFalse(data["is_image"])
        self.assertIsNone(data["extracted_amount"])
        self.assertIsNone(data["extracted_date"])
        self.assertIsNone(data["extracted_vendor"])
        self.assertIsNone(data["detected_currency"])
