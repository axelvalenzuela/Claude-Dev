"""JWT-based web authentication (accounts/jwt_auth.py) — see
docs/adr/0011-jwt-web-authentication.md. Covers what the rest of the
suite's Client.login()/force_login() calls never exercise, since those
bypass JWTLoginView and JWTAuthenticationMiddleware's cookie check
entirely by creating a session directly."""
from datetime import timedelta

from django.test import TestCase, override_settings
from django.urls import reverse

from accounts.jwt_auth import (
    ACCESS_COOKIE_NAME,
    REFRESH_COOKIE_NAME,
    generate_access_token,
    generate_refresh_token,
)
from accounts.models import BlacklistedToken, User


class JWTLoginTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123"
        )

    def test_login_sets_both_jwt_cookies(self):
        response = self.client.post(
            reverse("login"), {"username": "ana@example.com", "password": "clave123"}
        )
        self.assertIn(ACCESS_COOKIE_NAME, response.cookies)
        self.assertIn(REFRESH_COOKIE_NAME, response.cookies)
        self.assertTrue(response.cookies[ACCESS_COOKIE_NAME]["httponly"])
        self.assertTrue(response.cookies[REFRESH_COOKIE_NAME]["httponly"])

    def test_login_does_not_create_a_session(self):
        self.client.post(reverse("login"), {"username": "ana@example.com", "password": "clave123"})
        self.assertNotIn("_auth_user_id", self.client.session)


class JWTCookieAuthenticationTests(TestCase):
    """Authenticating a protected view purely from JWT cookies, with no
    call to Client.login()/force_login() at all — proving the portal
    genuinely no longer depends on a session to identify the user."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123"
        )

    def test_protected_view_accessible_with_a_valid_access_cookie(self):
        self.client.cookies[ACCESS_COOKIE_NAME] = generate_access_token(self.user)
        response = self.client.get(reverse("reports:list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.user)

    def test_protected_view_redirects_with_no_cookie_at_all(self):
        response = self.client.get(reverse("reports:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_garbage_access_cookie_is_rejected(self):
        self.client.cookies[ACCESS_COOKIE_NAME] = "not-a-real-token"
        response = self.client.get(reverse("reports:list"))
        self.assertEqual(response.status_code, 302)

    def test_expired_access_token_alone_is_rejected(self):
        with override_settings(JWT_ACCESS_TOKEN_LIFETIME=timedelta(seconds=-1)):
            self.client.cookies[ACCESS_COOKIE_NAME] = generate_access_token(self.user)
        response = self.client.get(reverse("reports:list"))
        self.assertEqual(response.status_code, 302)


class JWTSilentRefreshTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123"
        )

    def test_expired_access_with_valid_refresh_reauthenticates_and_reissues_access_cookie(self):
        with override_settings(JWT_ACCESS_TOKEN_LIFETIME=timedelta(seconds=-1)):
            expired_access = generate_access_token(self.user)
        self.client.cookies[ACCESS_COOKIE_NAME] = expired_access
        self.client.cookies[REFRESH_COOKIE_NAME] = generate_refresh_token(self.user)

        response = self.client.get(reverse("reports:list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.wsgi_request.user, self.user)
        self.assertIn(ACCESS_COOKIE_NAME, response.cookies)
        self.assertNotEqual(response.cookies[ACCESS_COOKIE_NAME].value, expired_access)

    def test_expired_refresh_token_does_not_reauthenticate(self):
        with override_settings(JWT_ACCESS_TOKEN_LIFETIME=timedelta(seconds=-1)):
            self.client.cookies[ACCESS_COOKIE_NAME] = generate_access_token(self.user)
        with override_settings(JWT_REFRESH_TOKEN_LIFETIME=timedelta(seconds=-1)):
            self.client.cookies[REFRESH_COOKIE_NAME] = generate_refresh_token(self.user)

        response = self.client.get(reverse("reports:list"))

        self.assertEqual(response.status_code, 302)


class JWTLogoutTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="ana@example.com", email="ana@example.com", password="clave123"
        )

    def test_logout_clears_both_cookies(self):
        self.client.post(reverse("login"), {"username": "ana@example.com", "password": "clave123"})

        response = self.client.post(reverse("logout"))

        self.assertEqual(response.cookies[ACCESS_COOKIE_NAME].value, "")
        self.assertEqual(response.cookies[REFRESH_COOKIE_NAME].value, "")

    def test_logout_blacklists_the_refresh_token(self):
        self.assertEqual(BlacklistedToken.objects.count(), 0)
        self.client.post(reverse("login"), {"username": "ana@example.com", "password": "clave123"})

        self.client.post(reverse("logout"))

        self.assertEqual(BlacklistedToken.objects.count(), 1)

    def test_a_blacklisted_refresh_token_can_no_longer_silently_reauthenticate(self):
        self.client.post(reverse("login"), {"username": "ana@example.com", "password": "clave123"})
        old_refresh_token = self.client.cookies[REFRESH_COOKIE_NAME].value
        self.client.post(reverse("logout"))

        # Simulate an attacker who captured the refresh token before logout
        # and replays it afterward — logout should have made it worthless.
        self.client.cookies[REFRESH_COOKIE_NAME] = old_refresh_token
        response = self.client.get(reverse("reports:list"))

        self.assertEqual(response.status_code, 302)


class AdminIgnoresPortalJWTCookieTests(TestCase):
    """A JWT cookie proves identity for the portal only — Django Admin
    keeps its own session-based login untouched (docs/adr/
    0011-jwt-web-authentication.md), so a valid portal JWT must not, by
    itself, grant access to /admin/."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            username="admin@example.com", email="admin@example.com", password="clave123"
        )

    def test_valid_portal_jwt_does_not_authenticate_the_admin_site(self):
        self.client.cookies[ACCESS_COOKIE_NAME] = generate_access_token(self.admin)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("admin:login"), response.url)
