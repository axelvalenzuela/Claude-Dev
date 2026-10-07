"""Wires Django's built-in login signals to LoginEvent, so every attempt —
successful or not, against a real account or not — is recorded without any
view having to remember to do it. Connected in accounts/apps.py:ready()."""
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from .models import LoginEvent, find_user_by_login_identifier


def _client_ip(request):
    if request is None:
        return None
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _user_agent(request):
    if request is None:
        return ""
    return request.META.get("HTTP_USER_AGENT", "")[:255]


@receiver(user_logged_in)
def record_successful_login(sender, request, user, **kwargs):
    LoginEvent.objects.create(
        user=user,
        email_attempted=user.email,
        success=True,
        ip_address=_client_ip(request),
        user_agent=_user_agent(request),
    )


@receiver(user_login_failed)
def record_failed_login(sender, credentials, request=None, **kwargs):
    # Normalized to the account's canonical email whenever what was typed
    # resolves to one (email or employee number, see
    # models.py:find_user_by_login_identifier) — otherwise every failed
    # attempt is logged under whichever identifier was actually typed, so
    # is_account_locked() sees one unified three-strikes count per account
    # no matter which identifier the last few attempts used.
    typed = credentials.get("username", "")
    matched_user = find_user_by_login_identifier(typed)
    LoginEvent.objects.create(
        user=None,
        email_attempted=matched_user.email if matched_user else typed,
        success=False,
        ip_address=_client_ip(request),
        user_agent=_user_agent(request),
    )
