# 0008 — Admin access model: is_staff-wide Users & Groups, manual provisioning, dual-identifier login

**Status:** Accepted

## Context

Admin access (who can review and approve expense reports) needs to be
tightly controlled — the org chart names exactly four people who should
ever hold it (Iris Cortez, Adrian Heymes, Karen Plascencia, Steffan
Widmer). At the same time, signup for a regular employee account should
have as little friction as possible, since onboarding shouldn't
bottleneck on an admin's availability. And whoever asks for admin access
needs an actual admin able to grant it — which requires that admin to be
able to reach the account they want to change.

## Decision

Three related choices, applied together:

1. **Public self-service signup stays open to anyone**
   (`accounts.views.SignUpView`), and **never** grants `is_staff` on its
   own — every account created through it is a plain employee, always.
2. **Becoming an admin is never self-service.** There is no "request
   admin access" flow in the app. An employee who needs it asks one of
   the four named people personally (documented on the Dashboard's
   Policies/Help tabs); that admin then grants it manually by editing the
   requester's `User` row (`is_staff`, plus either `is_superuser` or
   `supervised_department`).
3. **Any active `is_staff` account — not only `is_superuser` — can reach
   Users & Groups to do that granting** (`accounts/admin.py:
   StaffManagedAdminMixin`, applied to both `UserAdmin` and a
   re-registered `GroupAdmin`). A department admin like Adrian doesn't
   need to escalate to superuser status just to add a new admin; the
   `is_staff`-is-the-boundary principle from ADR 0004 extends here too.

A fourth, related piece: login accepts **either the account's email or
its company employee number**
(`accounts/backends.py:EmployeeNumberOrEmailBackend`), since people don't
reliably remember which one a given form wants. The account-lockout
counter (3 consecutive failed attempts) is normalized to the account's
canonical email regardless of which identifier a given attempt used
(`accounts/models.py:find_user_by_login_identifier`), so the three-strikes
count can't be dodged by alternating between the two.

## Alternatives considered

- **Only `is_superuser` accounts can manage Users & Groups** (Django's
  default): the initial state of this app, changed deliberately — it
  meant a department admin couldn't grant access to a new hire without
  going through the general admin every time, adding a dependency this
  org chart's actual four-admin size doesn't need.
- **A formal "request admin access" self-service flow** (a button an
  employee clicks, generating a request an admin approves in-app):
  considered and rejected — the org chart is four named, known people;
  building an approval workflow for a decision that's realistically made
  in a hallway conversation would be solving a problem this app doesn't
  have yet.
- **Login by email only** (no employee number): the simpler default, but
  employees already have to know their employee number for other
  reasons (it's printed on the RH-named exports, shown in their own
  profile) — accepting either avoids a real, observed point of friction
  without weakening the account-lockout protection, once the lockout
  counter was normalized to account for it.

## Consequences

- **Any of the four current admins can grant full `is_superuser` access
  to anyone**, including to themselves or to a brand-new account — this
  is the direct, accepted trade-off of choice 3. There's no
  reduced-permission tier (e.g. "can view but not edit `is_staff`") — if
  that granularity is ever needed, `StaffManagedAdminMixin` would need
  splitting into view-only vs. change-capable variants.
- The admin roster is enforced entirely by **process** (four named
  people, everyone else asks them personally), not by any code-level
  allowlist — nothing in the app prevents a fifth or sixth admin from
  being created if one of the four decides to grant it. This is
  intentional (flexibility for the org chart to actually change) but
  means the "only these four" boundary lives in `README.md`/the
  Policies tab, not in a constraint the code enforces.
- Login-by-employee-number required touching three places consistently
  (the auth backend, the lockout check, the failed-login audit log) —
  missing any one of them would have reopened the exact lockout-bypass
  gap this decision closed. `find_user_by_login_identifier()` exists
  specifically so there's one place that knows both identifiers are
  valid, not three places that each have to remember independently.
