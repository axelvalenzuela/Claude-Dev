"""Tests for the account-lockout brute-force protection and the password
reset flow that lifts it (see accounts/security.py, accounts/forms.py)."""
from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import LoginEvent, User
from .security import LOCKOUT_THRESHOLD, is_account_locked


class IsAccountLockedTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123"
        )

    def test_not_locked_with_no_history(self):
        self.assertFalse(is_account_locked("ana@example.com"))

    def test_not_locked_after_fewer_than_threshold_failures(self):
        for _ in range(LOCKOUT_THRESHOLD - 1):
            LoginEvent.objects.create(email_attempted="ana@example.com", success=False)
        self.assertFalse(is_account_locked("ana@example.com"))

    def test_locked_after_threshold_consecutive_failures(self):
        for _ in range(LOCKOUT_THRESHOLD):
            LoginEvent.objects.create(email_attempted="ana@example.com", success=False)
        self.assertTrue(is_account_locked("ana@example.com"))

    def test_not_locked_if_a_success_is_among_the_recent_events(self):
        LoginEvent.objects.create(email_attempted="ana@example.com", success=False)
        LoginEvent.objects.create(email_attempted="ana@example.com", success=True)
        LoginEvent.objects.create(email_attempted="ana@example.com", success=False)
        LoginEvent.objects.create(email_attempted="ana@example.com", success=False)
        self.assertFalse(is_account_locked("ana@example.com"))


class EmployeeLoginLockoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123"
        )

    def _fail_login(self):
        return self.client.post(reverse("login"), {"username": "ana@example.com", "password": "wrong"})

    def test_locks_out_after_three_failed_attempts(self):
        for _ in range(LOCKOUT_THRESHOLD):
            self._fail_login()

        # Correct password, but the account is now locked.
        response = self.client.post(
            reverse("login"), {"username": "ana@example.com", "password": "clave123"}
        )

        self.assertContains(response, "Too many failed login attempts")
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_reset_password_lifts_the_lockout(self):
        for _ in range(LOCKOUT_THRESHOLD):
            self._fail_login()
        self.assertTrue(is_account_locked("ana@example.com"))

        # Build the reset link the same way the emailed one would resolve to
        # (uid + token), rather than parsing the console-backend email body.
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        confirm_url = reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token})

        # First GET swaps the real token for a session-stored placeholder
        # (Django's usual anti-token-leak redirect) — follow it, then post.
        get_response = self.client.get(confirm_url, follow=True)
        post_url = get_response.redirect_chain[-1][0] if get_response.redirect_chain else confirm_url
        confirm_response = self.client.post(
            post_url, {"new_password1": "brand-new-pass-1", "new_password2": "brand-new-pass-1"}
        )
        self.assertEqual(confirm_response.status_code, 302)

        self.assertFalse(is_account_locked("ana@example.com"))

        login_response = self.client.post(
            reverse("login"), {"username": "ana@example.com", "password": "brand-new-pass-1"}
        )
        self.assertEqual(login_response.status_code, 302)


class AdminLoginLockoutTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin@example.com", email="admin@example.com", password="clave123"
        )

    def test_admin_login_locks_out_after_three_failed_attempts(self):
        for _ in range(LOCKOUT_THRESHOLD):
            self.client.post(
                reverse("admin:login"), {"username": "admin@example.com", "password": "wrong"}
            )

        response = self.client.post(
            reverse("admin:login"), {"username": "admin@example.com", "password": "clave123"}
        )

        self.assertContains(response, "Too many failed login attempts")
        self.assertFalse(response.wsgi_request.user.is_authenticated)
