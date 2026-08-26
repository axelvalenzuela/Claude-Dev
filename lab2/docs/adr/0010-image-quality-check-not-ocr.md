# 0010 — A lightweight image-quality check for photo receipts, not OCR

**Status:** Accepted

## Context

`expenses/pdf_analysis.py` already pre-fills a document's fields (amount,
type, date, vendor, currency) by reading a PDF's text layer — free,
since the text is already there in the file. A photo receipt (JPG/PNG)
has no text layer to read; getting the same pre-fill for a photo would
require actual optical character recognition. Separately, employees
asked for *some* useful automatic feedback on an attached photo, even
if it's not full pre-fill — specifically, being told when a photo is too
blurry or otherwise unusable to trust, instead of finding that out only
after an admin rejects the report.

## Decision

`expenses/image_analysis.py` adds a **quality check, not content
extraction**: it opens the photo with Pillow, confirms it's actually
readable, checks its resolution against a minimum usable size, and runs
a lightweight blur heuristic (edge-detection variance on a downscaled
grayscale copy — calibrated against synthetic sharp/blurred test images,
see the module's `BLUR_VARIANCE_THRESHOLD` comment). None of this reads
what's printed on the receipt — a photo's amount, vendor, and type
always still need to be typed in by hand. The live-preview endpoint
(`PreviewDocumentView`) runs this for every attached photo the same way
it runs `analyze_pdf` for every attached PDF, and the new-report page
shows the result as a note above that photo's fields — "looks clear
but can't be auto-read", "looks blurry/too small — please double-check
by eye", or "couldn't open this file at all" — always paired with an
explicit statement that the fields below are at their defaults.

## Alternatives considered

- **Real OCR via Tesseract**: would actually read the printed amount/
  vendor/type off a photo, matching what PDF text-extraction already
  does. Rejected specifically because Tesseract is a **system-level**
  binary dependency, not a pip wheel — every other dependency choice in
  this project has deliberately stayed pip-installable with no OS-level
  install step (see `docs/adr/0002-database-sqlite-then-postgres.md` and
  `docs/adr/0009-rule-based-help-chat.md` for the same reasoning applied
  to the database and the help chat respectively). Adding the one
  dependency in the whole app that needs a system package installed
  (and pinned/maintained per deployment OS) for one feature would be a
  meaningfully bigger operational commitment than anything else here.
- **A cloud OCR API** (Google Vision, AWS Textract, etc.): sidesteps the
  system-binary problem, but reintroduces exactly the trade-off already
  declined for the help chat — a real per-call cost and a hard internet
  dependency for a feature that currently works completely offline.
  Revisit if the company decides that trade-off is worth it for this
  specific feature.
- **No feedback on photos at all** (the prior behavior): simplest, but
  wastes the one thing that actually is easy and free to check — whether
  the photo is even legible — leaving a genuinely blurry upload
  undiscovered until much later.

## Consequences

- Pillow is now a real dependency (`requirements.txt`) — a pure pip
  wheel on every platform this app targets, no system package, no
  compiled extension to build from source. Consistent with the
  dependency bar every other library in this project already meets.
- The blur/size checks are heuristics, not a guarantee: an unusual photo
  could still read as "looks clear" while actually being illegible in a
  way the variance calculation doesn't catch, or vice versa. Acceptable
  because the fallback in both directions is the same — the employee (or
  the reviewing admin) still has to actually look at the photo before
  trusting it; this just surfaces an obvious problem earlier.
- A photo's amount/vendor/type fields are **never** pre-filled, no
  matter how sharp the photo is — this feature answers "is this photo
  worth trusting," not "what does this photo say." Revisit this ADR
  first if OCR (system Tesseract or a cloud API) is ever added later —
  it would change the second alternative above from declined to
  accepted, not just extend this one.
