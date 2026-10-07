# 0009 — A rule-based help-chat widget, not an LLM integration

**Status:** Accepted

## Context

Employees and admins both asked, informally, for a way to get quick
answers about how the platform works (the $60/day policy, how to
approve a report, how to attach a receipt) without digging through the
admin's Policies/Help tabs or the README. A floating, persistent chat
widget was the requested shape. The obvious modern way to build a "chat
that answers questions" is to call an LLM (e.g., the Claude API) — but
every fact this widget needs to answer with is already true and already
written down somewhere in this app's own documentation.

## Decision

The help-chat widget (`templates/help_chat/widget.html`,
`accounts/faq.py`, `accounts/help_chat_views.py`) is **rule-based**: a
fixed, hand-written set of question/answer entries (`FAQ_ENTRIES`),
matched to a user's free-text message by keyword overlap, filtered by
whether the asker is staff or not. No external API call, no model, no
network dependency for the feature to work.

"Rule-based" doesn't mean "static text only," though: a second set,
`DYNAMIC_ENTRIES`, covers the handful of questions whose true answer is
live data rather than a fixed fact — an employee's own employee number,
who a report's supervisor is, which reports are currently pending review
(scoped to the asking admin's department, same as everywhere else in the
app). Each dynamic entry has an `answer_fn(user)` instead of a fixed
string, read straight off the database at answer time — still no model
call, still fully deterministic and testable, just backed by a query
instead of a literal. A few *static* entries (the expense-type list, the
MXN/USD rate) also interpolate a real constant/model choice at answer
time rather than duplicating it as separate hardcoded text, so they can
never drift out of sync with `TravelDocument.DocType` or
`policies.USD_MXN_RATE` if either changes.

## Alternatives considered

- **Call the Claude API for real open-ended Q&A**: genuinely more
  capable — it would handle phrasing the fixed keyword list can't, and
  could answer questions this document doesn't anticipate. Rejected for
  this app specifically: it would require an `ANTHROPIC_API_KEY`, incur
  a real per-message cost, need internet access to function at all, and
  — for a tool whose answers are all just "what does this app already
  do" — risks a confident-sounding wrong answer where a rule-based miss
  just says "I don't know, ask an admin." It would also break this
  project's established "everything works with nothing but the app
  itself" posture (SQLite default, vendored Bootstrap, no CDN — see ADR
  0002's dependency-avoidance reasoning, which applies here just as
  much). Revisit this if the FAQ set outgrows what keyword matching can
  reasonably cover, or if the company decides the cost/infra tradeoff is
  worth it for genuinely open-ended questions.
- **No widget at all — point people at the existing Policies/Help
  tabs**: those tabs are admin-only today (inside `/admin/`), so an
  employee has no equivalent self-service reference at all. Rejected as
  incomplete — the ask was specifically for something available to both
  roles, everywhere in the app, not just admins inside one tab.

## Consequences

- Zero marginal cost per question, zero added infrastructure, and the
  feature keeps working if the server has no internet access at all —
  consistent with the rest of the app's dependency posture.
- The widget can only ever be as good as `FAQ_ENTRIES` — a real question
  about something not yet written down there gets the fallback message,
  never an improvised (and potentially wrong) answer. Extending it is a
  new entry in `accounts/faq.py`, not a prompt-engineering exercise.
- Matching is keyword overlap, not semantic understanding — an unusual
  phrasing of a covered topic can still miss and fall back. Acceptable
  given the fixed, small, well-known topic set this app actually has;
  would need revisiting (probably via the LLM alternative above) if the
  question surface grows much larger or more varied.
- Chat history is persisted per account (`HelpChatMessage`, one row per
  message, tied to `User`) so a conversation survives across sessions
  and devices until the user explicitly resets it — same durability
  expectation as every other per-account record in this app, and no
  different in kind whether the account is an employee's or an admin's.
- Dynamic answers never reveal more than the asker could already see
  through the normal UI: an employee's "my employee number"/"my
  supervisor"/"my recent activity" only ever reads their *own* rows, and
  an admin's "who owns the pending reports"/"recent activity" reuses the
  exact same department-scoping query `pending_reports_notification`
  already applies — the chat is a new way to ask, not a new grant of
  access. This is the guarantee every new dynamic entry has to preserve,
  not just the ones that existed when this ADR was written.
