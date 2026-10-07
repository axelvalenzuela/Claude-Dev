# 0012 — Incremental shared frontend JS modules, not a React rewrite

**Status:** Accepted

## Context

The user asked whether a React frontend would serve this app's growth
and long-term maintenance better than the current server-rendered Django
templates. Two concrete gaps had already been identified by request: the
"add a document" section of an existing draft report
(`report_detail.html`) still used a single-file, full-page-reload form,
while the New Report page (`report_form.html`) already had a drag-and-
drop, multi-file, live-preview uploader — and "My reports" had no way to
search once someone had accumulated many reports.

## Decision

**Stayed on server-rendered Django templates**, and fixed the actual gap
with a reusable, framework-free JS module instead of a rewrite:

- `static/js/document-uploader.js` — the drag-and-drop/multi-file/tab/
  live-preview logic (previously ~280 lines embedded directly in
  `report_form.html`) extracted into a standalone
  `initDocumentUploader(config)` function, taking element ids and the
  preview endpoint URL, returning `{ getSelectedFiles(), getPane(index),
  clearFiles() }`. Neither caller needs to know how it works internally.
- `expenses/templates/expenses/_document_uploader.html` — the drop
  zone, file input, and the two `<template>` elements (tab button, per-
  file field pane) extracted into one include, parameterized only by
  `doc_types` (already in both views' context).
- `report_form.html` (create) and `report_detail.html` (add to an
  existing draft) both now `{% include %}` that partial and call the
  same `initDocumentUploader()` — but each decides differently **what
  happens on submit**, which the module deliberately doesn't own:
  `report_form.html` lets the surrounding page-level form submit
  normally (title/description/supervisor/files all go together, exactly
  as `ReportCreateView.post` already expected); `report_detail.html`'s
  "Upload document(s)" button instead loops over the selected files and
  POSTs each one, in order, to the **existing, unmodified**
  `UploadDocumentView.post` — the same single-file endpoint that's
  worked (and been tested) since before this page had drag-and-drop —
  then reloads the page once all of them finish.
- `templates/base.html` gained a `{% block extra_js %}{% endblock %}`
  placed after the Bootstrap bundle `<script>` tag, specifically so a
  shared module like this one can load without every including template
  re-implementing the `DOMContentLoaded` deferral `report_form.html`
  needed when its script sat *before* that bundle tag in document order.
- Added a search box to `report_list.html` ("My reports"), shown only
  past 5 reports, reusing the exact same client-side substring-filter
  pattern already proven on the admin dashboard's Employees tab
  (`templates/admin/index.html`) — no new pattern invented for a problem
  that already had one.

## Alternatives considered

- **A React frontend** (what was actually asked about): rejected for
  this app's actual situation, not on principle. There is currently no
  API at all — every page is server-rendered HTML — so this would mean
  building a full Django REST Framework layer first, and then either
  rebuilding the entire reskinned Django Admin approval interface (tabs,
  KPI dashboard, colored status pills, hover animations, JWT-
  authenticated portal — see ADR 0011) from scratch in React, or running
  two frontends side by side indefinitely. For an internal tool this
  size, that's a large amount of new surface area and a second stack to
  maintain, for functionality gains mostly reachable more cheaply. It
  would make sense if this were growing into a customer-facing product
  with a dedicated frontend team — that isn't the trajectory here.
- **A second, batch-shaped upload endpoint** for `report_detail.html`
  (mirroring `ReportCreateView.post`'s `request.FILES.getlist("files")`
  + parallel-list pattern), instead of calling the existing single-file
  endpoint once per file: would have meant duplicating (and needing to
  keep in sync) the same validation logic
  (`services.build_travel_document`, `policies.validate_trip_span`) in
  two places, and changing a stable, already-tested endpoint's contract
  purely to serve a UI convenience the sequential-calls approach already
  delivers correctly. Rejected — YAGNI, and the existing tests covering
  `UploadDocumentView` (singular field names) didn't need to change at
  all as a result.
- **htmx/Alpine.js as a dependency**: would have handled some of this
  more declaratively, but the existing pattern (vanilla JS module + a
  small `init...()` call per page) was already established this session
  for the admin dashboard's tabs and search, and introducing a new
  client-side dependency for one more interactive widget wasn't
  justified by this specific gap.

## Consequences

- A bug fix or a new field in the uploader (say, a new document type, or
  a different preview note) now only has to happen in
  `document-uploader.js` and `_document_uploader.html` — previously it
  would have needed the same edit made twice, correctly, in two
  templates that could silently drift apart.
- `report_detail.html`'s document-adding flow is now N sequential
  requests instead of Django Admin's single-page-submit model — slightly
  slower for many files at once than a true batch endpoint would be, but
  correct, and not a regression from today's one-file-at-a-time
  behavior, which was already N requests (just N page reloads instead of
  N `fetch` calls).
- `ReportDetailView.get_context_data` dropped `upload_form`
  (`TravelDocumentForm()`, now unused) in favor of `doc_types` — the same
  context shape `ReportCreateView` already provides, which is what let
  both pages share one include.
- If this app's needs genuinely outgrow server-rendered templates later
  (a mobile app, a public API, a dedicated frontend team), this decision
  doesn't have to be revisited from scratch — a DRF API layer would still
  need to be built either way, and this ADR's alternatives section
  already captures why that wasn't the fork taken now.
