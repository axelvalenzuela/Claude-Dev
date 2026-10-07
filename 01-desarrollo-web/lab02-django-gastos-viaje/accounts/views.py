"""The views this app defines on top of Django's built-ins: public signup,
a JWT-issuing login/logout pair for the web portal (see accounts/
jwt_auth.py and docs/adr/0011-jwt-web-authentication.md), and a
password-reset-confirm that also lifts an account lockout. Most of the
reset flow is still Django's stock views, wired up directly in
accounts/urls.py — no need for a custom view class when there's no extra
behavior to add. Django Admin's own login/logout at /admin/ are untouched
and stay session-based; nothing here affects them."""
from django.contrib.auth import views as auth_views
from django.contrib.auth.signals import user_logged_in
from django.middleware.csrf import rotate_token
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView

from .forms import BrandedSetPasswordForm, LoginForm, SignUpForm
from .jwt_auth import clear_auth_cookies, revoke_refresh_token, set_auth_cookies
from .models import LoginEvent


class SignUpView(CreateView):
    """Public self-service registration for employees. Never grants staff
    access — that's reserved for the seeded admin account (see
    accounts/migrations/0002_seed_admin.py)."""

    form_class = SignUpForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("reports:list")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("reports:list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user = self.object
        rotate_token(self.request)
        user_logged_in.send(sender=self.object.__class__, request=self.request, user=self.object)
        set_auth_cookies(response, self.object)
        return response


class JWTLoginView(auth_views.LoginView):
    """Same form, same "?next=" handling, same redirect-if-already-
    authenticated behavior as Django's stock LoginView — only how a
    successful attempt is remembered changes: JWT cookies
    (accounts/jwt_auth.py) instead of a session."""

    form_class = LoginForm
    template_name = "accounts/login.html"

    def form_valid(self, form):
        user = form.get_user()
        self.request.user = user
        rotate_token(self.request)
        user_logged_in.send(sender=user.__class__, request=self.request, user=user)
        response = redirect(self.get_success_url())
        set_auth_cookies(response, user)
        return response


class JWTLogoutView(View):
    """POST-only, matching the logout <form> in templates/base.html.
    Clears both JWT cookies and blacklists the refresh token so it can't
    silently mint new access tokens after this point — see
    accounts/jwt_auth.py:revoke_refresh_token."""

    def post(self, request, *args, **kwargs):
        revoke_refresh_token(request)
        rotate_token(request)
        response = redirect("login")
        clear_auth_cookies(response)
        return response


class PasswordResetConfirmView(auth_views.PasswordResetConfirmView):
    """Same as Django's built-in view (sets the new password), plus: record
    a synthetic successful LoginEvent right when the reset completes. That's
    what actually lifts an account lockout (accounts/security.py checks the
    most recent LoginEvents) — otherwise resetting the password wouldn't by
    itself clear "too many failed attempts", since a reset alone doesn't log
    anything."""

    template_name = "registration/password_reset_confirm.html"
    form_class = BrandedSetPasswordForm

    def form_valid(self, form):
        response = super().form_valid(form)
        user = form.user
        LoginEvent.objects.create(
            user=user,
            email_attempted=user.email,
            success=True,
            ip_address=self.request.META.get("REMOTE_ADDR"),
            user_agent=self.request.META.get("HTTP_USER_AGENT", "")[:255],
        )
        return response
