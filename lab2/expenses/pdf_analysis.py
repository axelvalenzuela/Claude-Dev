"""Best-effort analysis of uploaded PDF receipts, run at upload time so
policy issues (wrong amount, wrong category) can be caught early instead of
only when a human reviews the report.

This is intentionally lightweight: it reads the PDF's text layer (no OCR, no
external binaries) and falls back to "nothing detected" for scanned/image
PDFs or any file it can't parse. It never blocks an upload on its own — it
only annotates the TravelDocument with what it found — except for the page
count, which the company treats as a hard limit (see validate_pdf_page_count).
"""
import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from pypdf import PdfReader
from pypdf.errors import PdfReadError

# Real-world travel receipts are 1-4 pages; the actual charge is almost
# always on page 1 or 2 (a boarding pass, hotel folio, ride receipt...).
MAX_PDF_PAGES = 4
PRIORITY_PAGE_COUNT = 2

AMOUNT_PATTERN = re.compile(r"\$?\s?(\d{1,3}(?:,\d{3})*(?:\.\d{2}))")

TYPE_KEYWORDS = {
    "flight": ("boarding pass", "e-ticket", "itinerary", "airline", "flight", "departure", "gate"),
    "hotel": ("hotel", "check-in", "check-out", "nightly rate", "room rate", "reservation"),
    "taxi": ("taxi", "uber", "lyft", "ride fare", "driver", "trip fare"),
    "meal": ("restaurant", "meal", "breakfast", "lunch", "dinner", "food", "menu", "server"),
}

# Ordered most-specific-first; a receipt only needs to match one of these to
# have its date guessed. Numeric formats cover the large majority of real
# receipts (boarding passes, hotel folios, ride receipts) — no dateutil
# dependency needed for that. A guessed date in the future is discarded (a
# misread digit, not a real receipt date).
DATE_CANDIDATE_PATTERNS = [
    (re.compile(r"\b\d{4}-\d{1,2}-\d{1,2}\b"), "%Y-%m-%d"),
    (re.compile(r"\b\d{1,2}/\d{1,2}/\d{4}\b"), "%m/%d/%Y"),
    (re.compile(r"\b\d{1,2}/\d{1,2}/\d{2}\b"), "%m/%d/%y"),
    (re.compile(r"\b\d{1,2}-\d{1,2}-\d{4}\b"), "%m-%d-%Y"),
]


@dataclass
class PdfAnalysisResult:
    extracted_amount: Decimal | None = None
    detected_type: str | None = None
    extracted_date: date | None = None
    extracted_vendor: str | None = None
    detected_currency: str | None = None


def validate_pdf_page_count(file):
    """Company policy: a travel receipt PDF must be at most MAX_PDF_PAGES
    pages. Non-PDF files and unreadable PDFs are left alone here — this only
    enforces the page count when it can actually be determined."""
    if not file.name.lower().endswith(".pdf"):
        return

    page_count = _safe_page_count(file)
    if page_count is not None and page_count > MAX_PDF_PAGES:
        raise ValidationError(
            f"This PDF has {page_count} pages; travel receipts must be at most "
            f"{MAX_PDF_PAGES} pages (the charge is normally on page 1 or 2)."
        )


def analyze_pdf(file_obj) -> PdfAnalysisResult:
    """Extract a likely total amount and expense category from a PDF's text.
    Prioritizes the first couple of pages, since that's where the actual
    charge normally is on a real receipt; falls back to the full document if
    nothing is found there. Returns an empty result (no exception) if the
    file isn't a readable PDF."""
    pages = _extract_pages(file_obj)
    if not pages:
        return PdfAnalysisResult()

    priority_text = "\n".join(pages[:PRIORITY_PAGE_COUNT])
    full_text = "\n".join(pages)

    amount = _guess_amount(priority_text)
    if amount is None:
        amount = _guess_amount(full_text)

    detected_type = _guess_type(priority_text)
    if detected_type is None:
        detected_type = _guess_type(full_text)

    extracted_date = _guess_date(priority_text) or _guess_date(full_text)
    extracted_vendor = _guess_vendor(pages)
    detected_currency = _guess_currency(priority_text) or _guess_currency(full_text)

    return PdfAnalysisResult(
        extracted_amount=amount,
        detected_type=detected_type,
        extracted_date=extracted_date,
        extracted_vendor=extracted_vendor,
        detected_currency=detected_currency,
    )


def _extract_pages(file_obj) -> list[str]:
    try:
        file_obj.seek(0)
        reader = PdfReader(file_obj)
        return [page.extract_text() or "" for page in reader.pages]
    except (PdfReadError, ValueError, OSError):
        return []
    finally:
        try:
            file_obj.seek(0)
        except (ValueError, OSError):
            pass


def _safe_page_count(file_obj) -> int | None:
    try:
        file_obj.seek(0)
        return len(PdfReader(file_obj).pages)
    except Exception:  # noqa: BLE001 - page-count check must never crash an upload
        return None
    finally:
        try:
            file_obj.seek(0)
        except (ValueError, OSError):
            pass


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


def _guess_date(text: str) -> date | None:
    for pattern, fmt in DATE_CANDIDATE_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        try:
            parsed = datetime.strptime(match.group(0), fmt).date()
        except ValueError:
            continue
        if parsed <= date.today():
            return parsed
    return None


def _guess_vendor(pages: list[str]) -> str | None:
    # A receipt's vendor/company name is almost always one of the first
    # few printed lines — this is a much rougher heuristic than the amount/
    # type detection (no keyword list to anchor on), so it's skipped
    # entirely rather than guessing wrong on an unusual layout: only a
    # short, letter-containing, non-numeric line counts as a candidate.
    if not pages:
        return None
    for line in pages[0].splitlines()[:8]:
        candidate = line.strip()
        if not (3 <= len(candidate) <= 60):
            continue
        if not re.search(r"[A-Za-z]{3,}", candidate):
            continue
        if AMOUNT_PATTERN.search(candidate):
            continue
        return candidate
    return None


def _guess_currency(text: str) -> str | None:
    lowered = text.lower()
    if "mxn" in lowered or "peso" in lowered or "mx$" in lowered:
        return "MXN"
    if "usd" in lowered or "us$" in lowered or "dollar" in lowered:
        return "USD"
    return None
