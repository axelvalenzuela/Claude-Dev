"""Best-effort *quality* analysis of an uploaded photo receipt (JPG/PNG),
run at upload time so a genuinely useless photo (too small to read, or
too blurry) gets flagged immediately — not just this heuristic:

This is deliberately **not OCR** — it never reads what's printed on the
photo (no amount, vendor, or expense type comes out of this module),
unlike expenses/pdf_analysis.py's text-layer reading of a PDF. Real OCR
would need either a system-level engine (Tesseract, a binary dependency
this project has otherwise avoided everywhere else — see
docs/adr/0002-database-sqlite-then-postgres.md and
docs/adr/0009-rule-based-help-chat.md for the same "avoid an unnecessary
external dependency" reasoning applied elsewhere) or a paid cloud OCR
API (real per-call cost and a hard internet dependency, the same
trade-off already declined for the help chat in ADR 0009). Pillow, by
contrast, is a pure pip wheel — no system binary, no network call, no
per-use cost — so it's the one part of "read something useful off a
photo" that fits this app's existing dependency posture. It answers a
narrower, still genuinely useful question instead: *is this photo even
legible enough to be worth trusting*, so a blurry or corrupt upload gets
called out immediately, at upload time, rather than only being noticed
much later when someone actually needs the receipt.
"""
from dataclasses import dataclass

from PIL import Image, ImageFilter, ImageStat, UnidentifiedImageError

# Below this on the shorter side, a phone photo is almost certainly a
# thumbnail/screenshot crop, not a usable receipt scan.
MIN_USABLE_DIMENSION = 400

# Resized to a fixed width before measuring "detail" so the same threshold
# means the same thing regardless of the original photo's resolution.
ANALYSIS_WIDTH = 600

# Below this, an edge-detected grayscale image is close to flat — the
# photo is most likely out of focus. Calibrated against the same
# synthetic high-contrast test image sharp and at increasing Gaussian
# blur radii: sharp measured ~5150, a mild blur (radius 1) ~2180, and
# blur radii 3 and up all measured under 260, flattening out around
# ~155-180 for very heavy blur (never all the way to 0 — residual noise
# keeps some variance regardless of how blurred the source is). 300
# comfortably separates "clearly blurred" from "sharp or only barely
# soft" without being close to either cluster.
BLUR_VARIANCE_THRESHOLD = 300


@dataclass
class ImageAnalysisResult:
    is_readable: bool = False
    width: int | None = None
    height: int | None = None
    is_blurry: bool = False


def analyze_image(file_obj) -> ImageAnalysisResult:
    """Opens the photo and checks whether it's actually legible — never
    raises, never blocks the upload; a file this can't even open just
    comes back as not readable, the same fail-open posture as
    pdf_analysis.analyze_pdf for an unreadable PDF."""
    try:
        file_obj.seek(0)
        with Image.open(file_obj) as image:
            image.load()
            width, height = image.size
            is_blurry = _is_blurry(image)
    except (UnidentifiedImageError, OSError, ValueError):
        return ImageAnalysisResult(is_readable=False)
    finally:
        try:
            file_obj.seek(0)
        except (ValueError, OSError):
            pass

    if min(width, height) < MIN_USABLE_DIMENSION:
        is_blurry = True  # too small to be legible either way

    return ImageAnalysisResult(is_readable=True, width=width, height=height, is_blurry=is_blurry)


def _is_blurry(image: Image.Image) -> bool:
    grayscale = image.convert("L")
    if grayscale.width > ANALYSIS_WIDTH:
        ratio = ANALYSIS_WIDTH / grayscale.width
        grayscale = grayscale.resize((ANALYSIS_WIDTH, max(1, int(grayscale.height * ratio))))

    edges = grayscale.filter(ImageFilter.FIND_EDGES)
    variance = ImageStat.Stat(edges).var[0]
    return variance < BLUR_VARIANCE_THRESHOLD
