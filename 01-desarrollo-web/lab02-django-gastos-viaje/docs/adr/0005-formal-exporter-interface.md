# 0005 — A formal exporter interface (ReportExporter ABC) for Excel/Word/History

**Status:** Accepted

## Context

The app generates downloadable documents from a report in more than one
format (Excel via openpyxl, Word via python-docx) and, later, a third
kind (a history/audit-trail document). Each format needs to be built,
served as a live preview, saved as a permanent snapshot on approval, and
downloaded later — four call sites (`finalize_approval`, the employee
download views, the admin preview routes, the admin history-download
route) that all needed the same "build → bytes → serve/save" sequence,
independently, once per format.

## Decision

`expenses/exporters.py` defines `ReportExporter`, an `ABC` with one
abstract method (`build(report)`) and a concrete `to_bytes(report)` built
on top of it. `ExcelExporter`, `WordExporter`, and `HistoryExporter` are
the only three classes that know how to turn a report into a specific
file format; every call site goes through one of the three module-level
instances (`excel_exporter`, `word_exporter`, `history_exporter`)
instead of repeating the build/serialize ceremony itself. `HistoryExporter`
deliberately doesn't participate in `finalize_approval`'s snapshot-saving
— it always builds live from the current audit trail, never from a saved
copy.

## Alternatives considered

- **A plain function per format, called directly from each site**: what
  existed before this decision — four near-identical "build a
  `BytesIO`, write it, set the content-type" blocks across two files,
  and the Word content-type hardcoded a second time. Rejected once the
  duplication was noticed, in favor of one shared shape.
- **A generic "renderer registry" keyed by string** (e.g.
  `EXPORTERS["excel"]`): more indirection for no real benefit — there
  are three formats, known and named at every call site already; a
  registry would trade explicit imports for a lookup that could fail at
  runtime with a typo'd key instead of at import time.

## Consequences

- Adding a fourth export format (e.g. PDF) is one new class in
  `exporters.py`; none of `services.py`, the views, or the admin routes
  need to change.
- Every call site's "what format, what bytes" logic is identical by
  construction — a bug fixed in `to_bytes()` (e.g. how the buffer is
  read) fixes it everywhere at once.
- The interface assumes every exporter's `build()` returns an object
  with a `.save(stream)` method (true of both openpyxl's `Workbook` and
  python-docx's `Document` without an adapter) — a future format whose
  library doesn't expose that shape would need a small wrapper, not a
  redesign of the interface itself.
