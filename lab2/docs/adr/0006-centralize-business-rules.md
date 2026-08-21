# 0006 — Every business rule lives in exactly one method, read everywhere else

**Status:** Accepted

## Context

The app has several business rules that need to be evaluated and shown
consistently across multiple, very different surfaces: the $60/day
spending policy (with a currency-conversion step and a flight/hotel
exemption), the 30-day submission deadline, the 21-day one-trip span
check, and the CEO approval clause. Each rule needed to appear on the
employee's report page, the admin's changelist and review page, and (for
the $60/day policy) the generated Excel and Word. An early version of
the $60/day check compared raw peso amounts against a dollar limit
directly on one surface, which produced incorrect flags nowhere else the
rule was (re-)implemented — a bug caused directly by the rule existing
in more than one place with slightly different logic each time.

## Decision

Each business rule is computed by exactly one method or constant, and
every surface that displays it calls that same method and only decides
*how* to render the result — never re-derives the logic. Concretely:
`ExpenseReport.daily_totals()` is the only place that decides
`over_limit`/`has_flight_or_hotel`/`total_usd` for the $60/day policy
(currency conversion included, via `TravelDocument.amount_usd`); deadline
and trip-span rules live in `expenses/policies.py`/`validators.py` as
named constants and validator functions, not inline conditionals
repeated per view.

## Alternatives considered

- **Each surface re-implementing the check it needs**: what actually
  happened before this was made a deliberate rule (see the currency bug
  above) — every re-implementation was a chance to drift from the
  others, and one did. Rejected once the actual cost was visible.
- **A generic "policy engine"** (rule objects registered somewhere,
  evaluated by name): more machinery than four concrete rules justify —
  a plain method/function per rule, called directly, is easier to trace
  from a bug report straight to the one place that could be wrong.

## Consequences

- Changing a rule (the daily limit, the exchange rate, which document
  types are exempt, the deadline window) is a one-line edit in
  `policies.py` or the one method that owns it — never touches
  `excel.py`, `word_export.py`, any admin file, or any template, all of
  which only read the result.
- Every surface stays consistent with every other **by construction**,
  not by discipline — there's no second copy of the $60/day logic that
  could be edited and forgotten. This is what made the July currency bug
  a one-place fix rather than a per-surface hunt once found (see
  `docs/ARCHITECTURE.md`'s "One rule, one place" section for the full
  story).
- Adding a rule with a genuinely different shape (not "threshold with an
  exemption," something with more states) means extending the return
  shape of the owning method (as `daily_totals()` did, adding
  `has_flight_or_hotel` alongside `over_limit`) — every caller still
  only reads fields, never recomputes, so this stays additive rather
  than a breaking change to callers.
