"""Local brute-force protection: lock an account out after too many
consecutive failed login attempts, using the LoginEvent audit trail that's
already recorded for every attempt (see accounts/signals.py) instead of
introducing a separate lockout-state field.

The lockout is lifted the moment the account has a successful LoginEvent
more recent than its last LOCKOUT_THRESHOLD failures — which happens
naturally on a correct login, and is also triggered deliberately by
completing a password reset (see accounts/views.py:PasswordResetConfirmView),
so "reset your password to regain access" is a real, working instruction.
"""
from .models import LoginEvent

# 3 wrong passwords in a row locks the account — matches the company's
# stated local security policy.
LOCKOUT_THRESHOLD = 3


def is_account_locked(email: str) -> bool:
    if not email:
        return False

    recent_events = list(
        LoginEvent.objects.filter(email_attempted__iexact=email).order_by("-created_at")[:LOCKOUT_THRESHOLD]
    )
    if len(recent_events) < LOCKOUT_THRESHOLD:
        return False

    return all(not event.success for event in recent_events)
