from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from .forms import BrandedSetPasswordForm, SignUpForm
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
        login(self.request, self.object)
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
