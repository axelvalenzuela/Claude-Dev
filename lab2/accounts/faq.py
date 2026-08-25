"""The help-chat widget's answer engine. Deliberately rule-based, not an
LLM call: every answer here is already true and already documented
(README.md, the admin's Policies/Help tabs) — matching a question to the
right canned answer needs no model, no API key, no per-message cost, and
no internet connection, which keeps this feature consistent with the
rest of the app (SQLite by default, vendored Bootstrap, no CDN — see
docs/adr/0002-database-sqlite-then-postgres.md's "no unnecessary external
dependency" spirit).

Matching is a simple keyword-overlap score, not fuzzy/semantic search —
good enough for a fixed, small set of known topics, and its behavior is
fully predictable and testable (see accounts/tests/test_help_chat.py).
Each entry's `audience` controls who ever sees it: "all" is shown to
both employees and admins, "employee"/"admin" only to that role — an
employee's chat should never suggest managing Users & Groups, and an
admin asking "how do I approve" shouldn't get an employee's submit-a-
report answer instead.
"""
import re

FALLBACK_ANSWER = (
    "I don't have an answer for that one. Check the Policies/Help tabs if "
    "you're an admin, or ask your supervisor/admin directly — see the "
    "README's admin-credentials section for who to contact."
)

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
        "audience": "employee",
        "keywords": ["currency", "peso", "pesos", "mxn", "dollar", "usd", "exchange", "rate"],
        "question": "Which currency should I pick for a receipt?",
        "answer": (
            "Pick whichever currency the receipt was actually issued in (USD "
            "or MXN) — don't convert it yourself. The app converts MXN to USD "
            "automatically (at a fixed rate) for the $60/day check and your "
            "report's total; your original peso amount is never changed."
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
        "keywords": ["login", "log", "email", "employee", "number", "password", "sign", "in"],
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
        "keywords": ["history", "download", "audit", "trail", "who", "when"],
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
]


def _tokenize(message: str) -> set:
    # Strips punctuation a real question naturally ends with ("...report?")
    # so it doesn't silently break an otherwise-exact keyword match.
    return set(re.findall(r"[a-z0-9]+", message.lower()))


def _score(message_words: set, keywords: list) -> int:
    return sum(1 for keyword in keywords if keyword in message_words)


def find_answer(message: str, *, is_staff: bool) -> str:
    """Matches a free-text question to the best FAQ_ENTRIES entry for this
    user's role, by keyword overlap. Returns FALLBACK_ANSWER if nothing
    scores above zero — never guesses at an answer that isn't already
    documented elsewhere in the app."""
    message_words = _tokenize(message)
    audiences = {"all", "admin"} if is_staff else {"all", "employee"}

    best_entry, best_score = None, 0
    for entry in FAQ_ENTRIES:
        if entry["audience"] not in audiences:
            continue
        score = _score(message_words, entry["keywords"])
        if score > best_score:
            best_entry, best_score = entry, score

    return best_entry["answer"] if best_entry else FALLBACK_ANSWER
