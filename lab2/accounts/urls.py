"""Auth routes under /accounts/: signup, login/logout, and the password
reset flow — the same one used by both the employee login and (via the
"Forgotten your password?" link in templates/admin/login.html) the admin
login, so there's a single reset flow for every account."""
from django.contrib.auth import views as auth_views
from django.urls import path

from .forms import BrandedPasswordResetForm, LoginForm
from .views import PasswordResetConfirmView, SignUpView

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="accounts/login.html", authentication_form=LoginForm),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),
    # Shared by the employee login and the Django Admin login ("Forgotten
    # your password?" on both points here) — one reset flow for every
    # account, admin or not. In local dev, EMAIL_BACKEND prints the reset
    # link to the console instead of sending a real email.
    path(
        "password-reset/",
        auth_views.PasswordResetView.as_view(
            template_name="registration/password_reset_form.html", form_class=BrandedPasswordResetForm
        ),
        name="password_reset",
    ),
    path(
        "password-reset/done/",
        auth_views.PasswordResetDoneView.as_view(template_name="registration/password_reset_done.html"),
        name="password_reset_done",
    ),
    path(
        "reset/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "reset/done/",
        auth_views.PasswordResetCompleteView.as_view(template_name="registration/password_reset_complete.html"),
        name="password_reset_complete",
    ),
]
