def make_image_bytes(*, width=800, height=1000, blur_radius=0) -> bytes:
    """A synthetic "receipt-like" JPEG — a high-contrast checkerboard
    pattern (stands in for printed text/lines without needing a real
    scanned receipt fixture), used by expenses/tests/test_image_analysis.py
    to exercise the sharp/blurry distinction. `blur_radius` > 0 simulates
    an out-of-focus photo (see expenses/image_analysis.py's calibration
    comment for how this was tuned against exactly this kind of image)."""
    from io import BytesIO

    from PIL import Image, ImageDraw, ImageFilter

    image = Image.new("L", (width, height), color=255)
    draw = ImageDraw.Draw(image)
    for y in range(0, height, 20):
        for x in range(0, width, 40):
            draw.rectangle([x, y, x + 20, y + 10], fill=0)
    image = image.convert("RGB")

    if blur_radius:
        image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    buffer = BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def make_pdf_bytes(page_texts) -> bytes:
    """Hand-rolled minimal PDF (one or more pages, each with a text-showing
    operator), just enough for pypdf's text/page-count reading — used instead
    of pulling in a full PDF writer dependency for a handful of tests.

    `page_texts` can be a single string (one-page PDF) or a list of strings
    (one page per string).
    """
    if isinstance(page_texts, str):
        page_texts = [page_texts]

    num_pages = len(page_texts)
    font_num = 3 + num_pages * 2
    kids = " ".join(f"{3 + i * 2} 0 R" for i in range(num_pages))

    body = b"%PDF-1.4\n"
    body += f"1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj\n".encode()
    body += f"2 0 obj<< /Type /Pages /Kids [{kids}] /Count {num_pages} >>endobj\n".encode()

    for i, text in enumerate(page_texts):
        page_obj = 3 + i * 2
        content_obj = page_obj + 1
        content = f"BT /F1 18 Tf 10 100 Td ({text}) Tj ET".encode()
        body += (
            f"{page_obj} 0 obj<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 {font_num} 0 R >> >> "
            f"/MediaBox [0 0 400 200] /Contents {content_obj} 0 R >>endobj\n"
        ).encode()
        body += f"{content_obj} 0 obj<< /Length {len(content)} >>\nstream\n".encode() + content + b"\nendstream\nendobj\n"

    body += f"{font_num} 0 obj<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>endobj\n".encode()
    body += b"trailer<< /Size 1 /Root 1 0 R >>\nstartxref\n0\n%%EOF\n"
    return body
