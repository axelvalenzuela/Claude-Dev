from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """App user. username = email; adds the employee's department."""

    department = models.CharField("Department", max_length=100, blank=True)

    def __str__(self):
        return self.get_full_name() or self.email or self.username


class LoginEvent(models.Model):
    """Session/login audit trail, for the admin's security & traceability view.

    Recorded for both successful and failed attempts (user is null on a
    failed attempt against an email that doesn't exist)."""

    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="login_events")
    email_attempted = models.CharField(max_length=255)
    success = models.BooleanField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        status = "success" if self.success else "failed"
        return f"{self.email_attempted} · {status} · {self.created_at:%Y-%m-%d %H:%M}"
