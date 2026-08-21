from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        from . import signals  # noqa: F401 - wires up LoginEvent recording

        self._brand_admin_site()
        self._start_auto_shutdown_timer()

    def _brand_admin_site(self):
        # Gives the Django Admin the same "MHP by Porsche" identity as the
        # employee portal, instead of the generic "Django administration",
        # and applies the same account-lockout rule to its login form.
        from django.conf import settings
        from django.contrib import admin

        from .forms import AdminLoginForm

        brand = f"{settings.PORTAL_BRAND_NAME} {settings.PORTAL_BRAND_TAGLINE}"
        admin.site.site_header = f"{brand} — Expense Approvals"
        admin.site.site_title = f"{settings.PORTAL_BRAND_NAME} Admin"
        admin.site.index_title = "Reports awaiting approval"
        admin.site.login_form = AdminLoginForm
        # Django's built-in left navigation tree (every registered app/model,
        # on every page) duplicates what the Dashboard's own tabs already
        # do on purpose (Employees / Reports / Users & Groups), and shows up
        # unwanted while reviewing a single report. Off everywhere, once,
        # instead of overriding nav-sidebar in every individual template.
        admin.site.enable_nav_sidebar = False

    def _start_auto_shutdown_timer(self):
        from .server_lifecycle import start_auto_shutdown_timer

        start_auto_shutdown_timer()
