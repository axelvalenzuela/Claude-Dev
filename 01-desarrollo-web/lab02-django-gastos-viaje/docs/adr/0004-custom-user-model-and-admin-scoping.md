# 0004 — Custom User model; is_staff-based admin scoping instead of per-model permissions

**Status:** Accepted

## Context

The app has two admin tiers that need different visibility into
submitted reports: a general/HR admin who approves reports from every
department, and a department admin who should only see and approve
their own department's reports. Django's built-in auth system offers a
fine-grained `Permission`/`Group` model for exactly this kind of access
control. The app also needed employee-specific identity data (a company
employee number, a department) that doesn't exist on Django's default
`User`.

## Decision

A custom `User` model (`accounts.User`, `AUTH_USER_MODEL`) adds
`employee_number`, `department`, and `supervised_department`. Report
visibility is decided by **`is_staff` plus `is_superuser`/
`supervised_department`**, checked directly in each `ModelAdmin`'s
`get_queryset()` (department filter) and `has_*_permission` methods
(`accounts/decorators.py:staff_permission` — any active `is_staff`
account passes) — **not** by assigning Django `Permission` objects or
`Group` memberships per admin. A department admin has zero explicit
`Permission` rows; their access is entirely a property of their `User`
row.

## Alternatives considered

- **Django's `Permission`/`Group` framework**: the "proper" fine-grained
  tool, and rejected specifically because it's fine-grained in a way
  this app doesn't need — there are exactly two admin tiers, not an open
  set of custom permission combinations, and modeling "sees only their
  own department" as a `Permission` would require either per-department
  `Permission` objects (awkward, doesn't scale with new departments) or
  a custom permission backend anyway (same complexity as the chosen
  approach, with an extra layer of indirection through `Group`/
  `Permission` rows that still wouldn't express "only their own
  department" on their own).
- **A separate `Role` model**: more flexible in the abstract, but this
  app has exactly two admin tiers today with no near-term need for a
  third — building a generic role system ahead of an actual requirement
  for one would be speculative.

## Consequences

- Adding or changing an admin's scope is a `User` row edit
  (`is_staff`/`is_superuser`/`supervised_department`), not a
  `Permission`/`Group` assignment — simpler to reason about for this
  app's two tiers, and directly editable from the `UserAdmin` form any
  `is_staff` account can already reach (see ADR 0008).
- Doesn't generalize past two tiers without new code: a third kind of
  scoped access (e.g. "sees two specific departments") would need a
  schema change (e.g. a many-to-many `supervised_departments`), not just
  a new `Group`. Acceptable now; would need revisiting if the org chart
  grows more complex than "general admin" vs. "one department each."
- Every `ModelAdmin` that should be staff-reachable has to explicitly
  wire up `staff_permission` (or equivalent scoping) itself — nothing
  enforces this globally the way Django's default permission checks
  would. Deliberately explicit — see ADR 0008 for the Users & Groups
  case specifically.
