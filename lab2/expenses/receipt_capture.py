"""Renders a receipt document (PDF or photo) to a PNG thumbnail — the one
place that knows how to turn *any* uploaded receipt into an image, used by
both word_export.py (embedding "Receipt captures" in the generated Word
document) and the admin's inline preview gallery (expenses/admin/reports.py:
preview_receipt), so a PDF invoice gets the same visual capture a photo
receipt already did, without either caller needing to know how.

Uses PyMuPDF (the `fitz` package) rather than a poppler-based tool
(pdf2image, etc.) specifically because it installs as a normal pip wheel —
no system-level dependency to install on whatever machine this app ends up
deployed on.
"""
import fitz

RENDER_DPI = 120


def render_receipt_thumbnail(file_field) -> bytes:
    """Returns PNG bytes for `file_field`: the first page rendered to an
    image if it's a PDF, or the image data itself unchanged if it's
    already a photo (JPG/PNG). Raises if the file can't be read or
    rendered — callers are expected to catch that and show a placeholder,
    the same way a corrupt/unreadable upload has always been handled here.
    """
    name = file_field.name.lower()
    file_field.open("rb")
    try:
        data = file_field.read()
    finally:
        file_field.close()

    if not name.endswith(".pdf"):
        return data

    with fitz.open(stream=data, filetype="pdf") as pdf:
        pixmap = pdf[0].get_pixmap(dpi=RENDER_DPI)
        return pixmap.tobytes("png")
