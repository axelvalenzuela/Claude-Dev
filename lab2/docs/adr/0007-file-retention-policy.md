# 0007 — Delete originals at approval; scheduled 90-day cleanup otherwise

**Status:** Accepted

## Context

Every uploaded receipt (PDF or photo) is a real file on disk
(`media/uploads/`). Keeping every original forever indefinitely grows
storage for files that, once a report is fully processed, are redundant
with the generated Excel/Word record. The policy on when files stop
being needed went through two earlier versions before landing here
(documented in the README for exactly this reason — so the "why" of the
current behavior doesn't get lost): originals were first never deleted,
then deleted at **submission**, before settling on deletion at
**approval**.

## Decision

Original receipt files are deleted **only once a report is approved**
(`expenses/services.py:finalize_approval`, inside the same transaction
as the approval itself) — at that point the generated Excel and Word
(which embed an image capture of every receipt, not just a reference to
it) become the permanent record, so nothing is actually lost. A report
that's *never* approved (stays pending, or is rejected — there's no
resubmit flow) keeps its original files until they're 90 days old
(`FILE_RETENTION_DAYS`, `expenses/policies.py`), at which point a
Django management command (`cleanup_old_documents`), scheduled externally
(cron/Task Scheduler/a Docker sidecar — see `docs/DEPLOYMENT.md`),
deletes just the file — the `TravelDocument` row, and the report itself,
are never touched.

## Alternatives considered

- **Delete at submission** (the previous behavior): rejected because an
  admin or the employee might still need to look at the original file
  while a report is under review, before a decision is made — deleting
  it at submission removed that option during exactly the window it
  would have mattered most.
- **Never delete anything**: rejected as unbounded storage growth for
  files that, once approved, are redundant with the permanent Excel/Word
  record — and, for reports that are rejected or abandoned, files with
  no clear reason to be kept forever.
- **Running cleanup automatically inside request handling** (e.g. on
  every login or every dashboard load): rejected as the wrong place for
  a maintenance task — it would tie an unrelated, potentially slow
  operation to normal request/response cycles instead of a predictable,
  independently-schedulable job.

## Consequences

- An approved report's permanent record is the Excel/Word pair, not the
  originals — anything not captured in those two files (e.g. a receipt
  detail visible only in a part of a PDF not rendered by
  `receipt_capture.py`) is genuinely gone after approval. Acceptable
  because the capture step runs before deletion and captures the whole
  first page/photo, not a crop.
- The 90-day cleanup is **not automatic** — it depends on whoever
  operates the deployment actually scheduling `cleanup_old_documents`
  (cron, Task Scheduler, or a container sidecar). A deployment that
  skips this step simply keeps pending/rejected originals forever,
  silently, since nothing else in the app enforces the 90-day window.
- The report row, its data (type, amount, date), and the audit trail
  survive file deletion either way — only the `FileField` empties out —
  so the $60/day breakdown, the history download, and every other report
  view keep working identically before and after either kind of
  cleanup.
