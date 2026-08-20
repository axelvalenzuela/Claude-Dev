from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserCreationForm

from .models import User, generate_employee_number
from .security import LOCKOUT_THRESHOLD, is_account_locked


class LockoutCheckMixin:
    """Blocks a login attempt outright once the account has
    LOCKOUT_THRESHOLD consecutive failed attempts — checked before the
    password is even verified, so a locked account stays locked even if the
    *correct* password is entered on this attempt. See accounts/security.py
    for how the lockout is computed and lifted."""

    def clean(self):
        username = self.cleaned_data.get("username")
        if username and is_account_locked(username):
            raise forms.ValidationError(
                f"Too many failed login attempts ({LOCKOUT_THRESHOLD} in a row). "
                f"Reset your password to regain access.",
                code="locked",
            )
        return super().clean()


class LoginForm(LockoutCheckMixin, AuthenticationForm):
    username = forms.CharField(
        label="Email", widget=forms.TextInput(attrs={"class": "form-control", "autofocus": True})
    )
    password = forms.CharField(
        label="Password", widget=forms.PasswordInput(attrs={"class": "form-control"})
    )


class AdminLoginForm(LockoutCheckMixin, AdminAuthenticationForm):
    """Same lockout as the employee-facing LoginForm, wired into Django
    Admin's own login (see accounts/apps.py: admin.site.login_form)."""


class BrandedPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].widget.attrs["class"] = "form-control"


class BrandedSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(label="Full name", max_length=150)
    email = forms.EmailField(label="Email")
    department = forms.CharField(label="Department", max_length=100)

    class Meta:
        model = User
        fields = ("first_name", "department", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with that email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data["email"]
        user.email = self.cleaned_data["email"]
        user.employee_number = generate_employee_number()
        if commit:
            user.save()
        return user
