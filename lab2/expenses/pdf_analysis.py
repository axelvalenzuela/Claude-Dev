"""Best-effort analysis of uploaded PDF receipts, run at upload time so
policy issues (wrong amount, wrong category) can be caught early instead of
only when a human reviews the report.

This is intentionally lightweight: it reads the PDF's text layer (no OCR, no
external binaries) and falls back to "nothing detected" for scanned/image
PDFs or any file it can't parse. It never blocks an upload — it only
annotates the TravelDocument with what it found, so the employee/admin can
double check.
"""
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation

from pypdf import PdfReader
from pypdf.errors import PdfReadError

AMOUNT_PATTERN = re.compile(r"\$?\s?(\d{1,3}(?:,\d{3})*(?:\.\d{2}))")

TYPE_KEYWORDS = {
    "flight": ("boarding pass", "e-ticket", "itinerary", "airline", "flight", "departure", "gate"),
    "hotel": ("hotel", "check-in", "check-out", "nightly rate", "room rate", "reservation"),
    "taxi": ("taxi", "uber", "lyft", "ride fare", "driver", "trip fare"),
    "meal": ("restaurant", "meal", "breakfast", "lunch", "dinner", "food", "menu", "server"),
}


@dataclass
class PdfAnalysisResult:
    extracted_amount: Decimal | None = None
    detected_type: str | None = None


def analyze_pdf(file_obj) -> PdfAnalysisResult:
    """Extract a likely total amount and expense category from a PDF's text.
    Returns an empty result (no exception) if the file isn't a readable PDF."""
    text = _extract_text(file_obj)
    if not text:
        return PdfAnalysisResult()

    return PdfAnalysisResult(
        extracted_amount=_guess_amount(text),
        detected_type=_guess_type(text),
    )


def _extract_text(file_obj) -> str:
    try:
        file_obj.seek(0)
        reader = PdfReader(file_obj)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except (PdfReadError, ValueError, OSError):
        return ""
    finally:
        try:
            file_obj.seek(0)
        except (ValueError, OSError):
            pass
    return text


def _guess_amount(text: str) -> Decimal | None:
    matches = AMOUNT_PATTERN.findall(text)
    if not matches:
        return None

    amounts = []
    for match in matches:
        try:
            amounts.append(Decimal(match.replace(",", "")))
        except InvalidOperation:
            continue

    # Heuristic: on a typical receipt the total is the largest amount printed
    # (bigger than any per-item line or tax breakdown).
    return max(amounts) if amounts else None


def _guess_type(text: str) -> str | None:
    lowered = text.lower()
    best_type, best_score = None, 0

    for doc_type, keywords in TYPE_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > best_score:
            best_type, best_score = doc_type, score

    return best_type
