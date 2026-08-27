"""The help-chat widget's answer engine. Deliberately rule-based, not an
LLM call: every answer here is either a fact already documented (README,
the admin's Policies/Help tabs) or read live off the database at answer
time — matching a question to the right answer needs no model, no API
key, no per-message cost, and no internet connection, which keeps this
feature consistent with the rest of the app (SQLite by default, vendored
Bootstrap, no CDN — see docs/adr/0002-database-sqlite-then-postgres.md's
"no unnecessary external dependency" spirit, and
docs/adr/0009-rule-based-help-chat.md for the full reasoning).

Matching is a simple keyword-overlap score, not fuzzy/semantic search —
good enough for a fixed, small set of known topics, and its behavior is
fully predictable and testable (see accounts/tests/test_help_chat.py).
Each entry's `audience` controls who ever sees it: "all" is shown to
both employees and admins, "employee"/"admin" only to that role — an
employee's chat should never suggest managing Users & Groups, and an
admin asking "how do I approve" shouldn't get an employee's submit-a-
report answer instead.

Two kinds of entries:
- **FAQ_ENTRIES**: a fixed `answer` string, same for everyone who
  matches. A few of these interpolate a policy constant (the MXN/USD
  rate, the expense-type list) directly from where that constant is
  defined, rather than duplicating the number/list as separate text that
  could quietly drift out of sync if the constant ever changes.
- **DYNAMIC_ENTRIES**: an `answer_fn(user)` instead of a fixed string —
  for the handful of questions whose true answer depends on *who's
  asking* or on data that changes over time (an employee's own number,
  who a report's supervisor is, which reports are pending review right
  now, recent activity on the reports they can see). These read the
  database directly, scoped the same way every other admin/employee view
  in this app scopes it — an admin's "who owns the pending reports" (and
  "recent activity") answer only covers their own department unless
  they're HR/general.
"""
import re

from expenses.policies import USD_MXN_RATE

FALLBACK_ANSWER = (
    "I don't have an answer for that one. Check the Policies/Help tabs if "
    "you're an admin, or ask your supervisor/admin directly — see the "
    "README's admin-credentials section for who to contact."
)


def _expense_type_labels() -> str:
    from expenses.models import TravelDocument

    return ", ".join(label for _, label in TravelDocument.DocType.choices)


FAQ_ENTRIES = [
    {
        "audience": "employee",
        "keywords": ["create", "new", "start", "report", "trip"],
        "question": "How do I create a new expense report?",
        "answer": (
            "Go to My reports → \"+ New report\", fill in the trip details, "
            "and attach your receipts (PDF or photo) — you can attach several "
            "at once. Save as draft to keep editing, or submit right away."
        ),
    },
    {
        "audience": "employee",
        "keywords": ["upload", "attach", "receipt", "pdf", "photo", "picture"],
        "question": "How do I attach receipts?",
        "answer": (
            "Drag files onto the upload box (or click it to browse) — PDF or "
            "photo, several at once. A PDF's amount and expense type are "
            "detected automatically as a live preview; double-check it before "
            "submitting. Photos need the type and amount entered manually."
        ),
    },
    {
        "audience": "all",
        "keywords": ["expense", "types", "categories", "kind", "taxi", "meal", "flight", "hotel"],
        "question": "What expense types can I use for a document?",
        # Reads the model's own choices, so this can never list a type the
        # form itself doesn't actually offer, or miss one that was added.
        "answer": lambda: f"Every travel document is tagged with a type: {_expense_type_labels()} — pick whichever matches the receipt.",
    },
    {
        "audience": "employee",
        "keywords": ["currency", "peso", "pesos", "mxn", "dollar", "usd", "exchange", "rate"],
        "question": "Which currency should I pick for a receipt, and what's the exchange rate?",
        "answer": lambda: (
            f"Pick whichever currency the receipt was actually issued in (USD "
            f"or MXN) — don't convert it yourself. If it's MXN, the app "
            f"converts it to USD automatically at a fixed rate of "
            f"{USD_MXN_RATE} pesos per dollar (the default/only rate this "
            f"tool uses — there's no per-receipt rate to look up) for the "
            f"$60/day check and your report's total; a USD receipt just uses "
            f"a 1:1 rate. Your original amount is never changed, only "
            f"compared."
        ),
    },
    {
        "audience": "all",
        "keywords": ["60", "policy", "limit", "daily", "day", "violation", "flag", "exceed"],
        "question": "What's the $60/day policy?",
        "answer": (
            "Any day whose total (converted to USD) goes over $60 gets "
            "flagged — except a day with a flight or hotel charge, which "
            "routinely clears $60 on its own and is shown as justified, not "
            "as a violation."
        ),
    },
    {
        "audience": "employee",
        "keywords": ["deadline", "30", "days", "late", "expire", "submit", "window"],
        "question": "Is there a deadline to submit a report?",
        "answer": (
            "Yes — 30 days from the trip's flight date (or its earliest "
            "document date, if there's no flight). Past that, you can't "
            "submit it; the documents stay on the report as a draft."
        ),
    },
    {
        "audience": "employee",
        "keywords": ["one", "trip", "span", "21", "combine", "separate"],
        "question": "Can I combine two trips into one report?",
        "answer": (
            "No — every document on a report must fall within 21 days of the "
            "others. Receipts from two unrelated trips need two separate "
            "reports."
        ),
    },
    {
        "audience": "employee",
        "keywords": ["status", "track", "where", "approved", "rejected", "pending", "history"],
        "question": "How do I see if my report was approved?",
        "answer": (
            "Check My reports (status badge on each row) or History for the "
            "full list with the reviewer's note. You'll also see a banner the "
            "next time you load any page once a report you submitted is "
            "reviewed."
        ),
    },
    {
        "audience": "employee",
        "keywords": ["download", "excel", "word", "docx", "xlsx", "export", "file"],
        "question": "Where do I download my approved report?",
        "answer": (
            "Open the report once it's approved — the Excel and Word download "
            "buttons are right there. The originals you uploaded are removed "
            "at that point; the Excel/Word pair becomes the permanent record."
        ),
    },
    {
        "audience": "all",
        "keywords": ["login", "log", "email", "password", "sign", "in"],
        "question": "Can I log in with my employee number instead of my email?",
        "answer": (
            "Yes — the login field accepts either your email or your company "
            "employee number, whichever you remember."
        ),
    },
    {
        "audience": "all",
        "keywords": ["locked", "lockout", "forgot", "reset", "wrong", "attempts"],
        "question": "I'm locked out after failed login attempts — what do I do?",
        "answer": (
            "Use \"Forgot your password?\" on the login page. Completing a "
            "password reset lifts the lockout automatically — no need to "
            "contact anyone."
        ),
    },
    {
        "audience": "employee",
        "keywords": ["signup", "sign", "up", "register", "account"],
        "question": "How does a new employee register?",
        "answer": (
            "Anyone can self-register at the Sign up page — no invitation "
            "needed. New accounts are always regular employees; becoming an "
            "admin is a separate, personal request (see the next question if "
            "you're an admin)."
        ),
    },
    {
        "audience": "admin",
        "keywords": ["approve", "reject", "review", "decision", "ceo", "clause"],
        "question": "How do I approve or reject a report?",
        "answer": (
            "Open the report → Review tab → set Status, add a note (required "
            "to reject), check the CEO clause box (required to approve) → "
            "Save."
        ),
    },
    {
        "audience": "admin",
        "keywords": ["department", "scope", "adrian", "ics", "see", "only"],
        "question": "Why do I only see some departments' reports?",
        "answer": (
            "That's department-scoped access working as intended. Only the "
            "HR/general admins (Iris, Karen, Steffan) see every department — "
            "a department admin only sees their own."
        ),
    },
    {
        "audience": "admin",
        "keywords": ["admin", "access", "grant", "permission", "users", "groups", "staff", "promote"],
        "question": "How do I give someone admin access?",
        "answer": (
            "There's no self-service request flow on purpose. Once they've "
            "asked you personally, open Users & Groups → their account → "
            "check is_staff, then set either is_superuser (general admin) or "
            "supervised_department (department admin) — never both."
        ),
    },
    {
        "audience": "admin",
        "keywords": ["history", "download", "audit", "trail", "when"],
        "question": "Where can I see a report's full history?",
        "answer": (
            "Open the report → History tab for the on-screen log, or use the "
            "\"Download history\" button (top of the page) for a .docx with "
            "every status change, who made it, and any note — rejection "
            "notes included."
        ),
    },
    {
        "audience": "admin",
        "keywords": ["retention", "90", "delete", "file", "cleanup", "storage"],
        "question": "How long are uploaded files kept?",
        "answer": (
            "Originals are deleted once a report is approved (the Excel/Word "
            "pair becomes the permanent record). A report that's never "
            "approved keeps its files for 90 days, then a scheduled cleanup "
            "job removes just the file — the report and its data stay."
        ),
    },
    {
        "audience": "all",
        # Deliberately excludes generic words like "what"/"how"/"does" —
        # those appear in nearly every other question here too, and this
        # entry should only win when someone is actually asking about the
        # app/portal itself in general terms, not stealing a tied score
        # from a more specific entry on an unrelated question that just
        # happens to also start with "how".
        "keywords": ["portal", "platform", "app", "overview", "started", "beginner", "lost", "confused"],
        "question": "What is this platform for, generally?",
        "answer": (
            "This is the travel-expense-report portal: employees create a "
            "report, attach their receipts, and submit it; their supervisor "
            "reviews it in the admin and approves or rejects it. Ask me about "
            "a specific step (creating a report, attaching receipts, the "
            "$60/day policy, approving/rejecting) for more detail, or ask "
            "\"what's my recent activity\" to see what's happened lately."
        ),
    },
]


def _employee_number_answer(user) -> str:
    if user.employee_number:
        return f"Your employee number is {user.employee_number}."
    return "You don't have an employee number on file — that's unusual; contact an admin."


def _supervisor_answer(user) -> str:
    from expenses.models import ExpenseReport

    latest = ExpenseReport.objects.filter(user=user).order_by("-created_at").first()
    if not latest or not latest.supervisor_name:
        return (
            "Supervisor isn't a fixed field on your account — it's entered "
            "per report when you create one, and you don't have a report "
            "with a supervisor on file yet."
        )
    contact = f" ({latest.supervisor_email})" if latest.supervisor_email else ""
    return f"On your most recent report (\"{latest.title}\"), the supervisor on file is {latest.supervisor_name}{contact}."


def _pending_owners_answer(user) -> str:
    from expenses.models import ExpenseReport

    pending = ExpenseReport.objects.filter(status=ExpenseReport.Status.SUBMITTED).select_related("user")
    if not user.is_superuser and user.supervised_department:
        pending = pending.filter(user__department=user.supervised_department)

    owners = sorted({report.user.get_full_name() or report.user.email for report in pending})
    if not owners:
        return "No reports are currently pending review (in your scope)."
    return "Reports are currently pending review from: " + ", ".join(owners) + "."


RECENT_ACTIVITY_LIMIT = 5


def _format_activity_lines(entries) -> str:
    return "\n".join(
        f"{entry.created_at:%b %d} — {entry.get_action_display()} on “{entry.report.title}”"
        for entry in entries
    )


def _recent_activity_answer_employee(user) -> str:
    from expenses.models import ExpenseReportAuditLog

    entries = (
        ExpenseReportAuditLog.objects.filter(report__user=user)
        .select_related("report")
        .order_by("-created_at")[:RECENT_ACTIVITY_LIMIT]
    )
    if not entries:
        return "No activity yet — create a report to get started."
    return "Your most recent activity:\n" + _format_activity_lines(entries)


def _recent_activity_answer_admin(user) -> str:
    from expenses.models import ExpenseReportAuditLog

    # Same department-scoping rule as _pending_owners_answer above (and
    # everywhere else in the app an admin sees report-shaped data) — an
    # admin's "recent activity" is never a way to see more than the
    # Dashboard/Reports tabs would already show them.
    entries = ExpenseReportAuditLog.objects.select_related("report", "report__user").order_by("-created_at")
    if not user.is_superuser and user.supervised_department:
        entries = entries.filter(report__user__department=user.supervised_department)
    entries = entries[:RECENT_ACTIVITY_LIMIT]

    if not entries:
        return "No recent activity on reports in your scope."
    return "Recent activity in your scope:\n" + _format_activity_lines(entries)


DYNAMIC_ENTRIES = [
    {
        "audience": "all",
        "keywords": ["my", "employee", "number"],
        "question": "What's my employee number?",
        "answer_fn": _employee_number_answer,
    },
    {
        "audience": "employee",
        "keywords": ["my", "supervisor", "manager", "reviewer", "boss"],
        "question": "Who is my supervisor?",
        "answer_fn": _supervisor_answer,
    },
    {
        "audience": "admin",
        "keywords": ["who", "owns", "owners", "pending", "waiting"],
        "question": "Who owns the reports currently pending review?",
        "answer_fn": _pending_owners_answer,
    },
    {
        "audience": "employee",
        "keywords": ["recent", "activity", "activities", "latest", "lately", "happened"],
        "question": "What's my recent activity?",
        "answer_fn": _recent_activity_answer_employee,
    },
    {
        "audience": "admin",
        "keywords": ["recent", "activity", "activities", "latest", "lately", "happened"],
        "question": "What's the recent activity on reports I can see?",
        "answer_fn": _recent_activity_answer_admin,
    },
]


def _tokenize(message: str) -> set:
    # Strips punctuation a real question naturally ends with ("...report?")
    # so it doesn't silently break an otherwise-exact keyword match.
    return set(re.findall(r"[a-z0-9]+", message.lower()))


def _score(message_words: set, keywords: list) -> int:
    return sum(1 for keyword in keywords if keyword in message_words)


def find_answer(message: str, *, user) -> str:
    """Matches a free-text question to the best entry (dynamic first, then
    static) for this user's role, by keyword overlap. Returns
    FALLBACK_ANSWER if nothing scores above zero — never guesses at an
    answer that isn't already documented, or isn't a real live lookup,
    elsewhere in the app."""
    message_words = _tokenize(message)
    audiences = {"all", "admin"} if user.is_staff else {"all", "employee"}

    best_entry, best_score, best_is_dynamic = None, 0, False
    for entry in DYNAMIC_ENTRIES + FAQ_ENTRIES:
        if entry["audience"] not in audiences:
            continue
        score = _score(message_words, entry["keywords"])
        if score > best_score:
            best_entry, best_score = entry, score
            best_is_dynamic = "answer_fn" in entry

    if best_entry is None:
        return FALLBACK_ANSWER
    if best_is_dynamic:
        return best_entry["answer_fn"](user)
    # A handful of static entries interpolate a live policy constant
    # (the FX rate, the expense-type list) via a zero-arg lambda instead
    # of a fixed string — call it if that's what this entry has.
    answer = best_entry["answer"]
    return answer() if callable(answer) else answer
