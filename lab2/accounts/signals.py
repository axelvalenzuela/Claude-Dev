"""Wires Django's built-in login signals to LoginEvent, so every attempt —
successful or not, against a real account or not — is recorded without any
view having to remember to do it. Connected in accounts/apps.py:ready()."""
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

from .models import LoginEvent


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
    LoginEvent.objects.create(
        user=None,
        email_attempted=credentials.get("username", ""),
        success=False,
        ip_address=_client_ip(request),
        user_agent=_user_agent(request),
    )
