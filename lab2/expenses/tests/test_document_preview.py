"""PreviewDocumentView (expenses/views/documents.py): the AJAX endpoint
that analyzes an attached PDF live, before anything is saved."""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from accounts.models import User
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

    def test_preview_document_skips_non_pdf_files(self):
        response = self.client.post(
            reverse("reports:preview_document"),
            {"file": SimpleUploadedFile("photo.jpg", b"fake-image", content_type="image/jpeg")},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["is_pdf"])
        self.assertIsNone(data["extracted_amount"])
