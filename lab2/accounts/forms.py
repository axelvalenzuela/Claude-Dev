"""Every auth-related form in the app: login (employee + admin, both with
the lockout check), signup, and the branded password-reset forms. Kept in
one module since none of them is large and they're all part of the same
"how does someone authenticate" story — split further only if one of them
grows enough to justify its own file."""
from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm, UserCreationForm

from .models import User, find_user_by_login_identifier, generate_employee_number
from .security import LOCKOUT_THRESHOLD, is_account_locked


class LockoutCheckMixin:
    """Blocks a login attempt outright once the account has
    LOCKOUT_THRESHOLD consecutive failed attempts — checked before the
    password is even verified, so a locked account stays locked even if the
    *correct* password is entered on this attempt. See accounts/security.py
    for how the lockout is computed and lifted.

    Login now accepts email or employee number
    (accounts/backends.py:EmployeeNumberOrEmailBackend) — resolving
    whatever was typed to the account's canonical email before checking is
    what keeps the lockout count on one account unified regardless of
    which identifier a given attempt used (see
    models.py:find_user_by_login_identifier), instead of splitting into
    two separate three-strikes counters that could be used to dodge it."""

    def clean(self):
        username = self.cleaned_data.get("username")
        if username:
            matched_user = find_user_by_login_identifier(username)
            lockout_key = matched_user.email if matched_user else username
            if is_account_locked(lockout_key):
                raise forms.ValidationError(
                    f"Too many failed login attempts ({LOCKOUT_THRESHOLD} in a row). "
                    f"Reset your password to regain access.",
                    code="locked",
                )
        return super().clean()


class LoginForm(LockoutCheckMixin, AuthenticationForm):
    username = forms.CharField(
        label="Email or employee number",
        widget=forms.TextInput(attrs={"class": "form-control", "autofocus": True}),
    )
    password = forms.CharField(
        label="Password", widget=forms.PasswordInput(attrs={"class": "form-control"})
    )


class AdminLoginForm(LockoutCheckMixin, AdminAuthenticationForm):
    """Same lockout as the employee-facing LoginForm, wired into Django
    Admin's own login (see accounts/apps.py: admin.site.login_form)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Email or employee number"


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
