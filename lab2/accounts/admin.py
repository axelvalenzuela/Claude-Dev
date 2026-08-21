"""Django Admin registrations for the accounts app: the User admin (with
the company-specific fields), a re-registered Group admin, and the
read-only LoginEvent audit trail. Expense-report approval lives in
expenses/admin/ instead — this module is only about the accounts
themselves."""
from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .decorators import staff_permission
from .models import LoginEvent, User, generate_employee_number


class StaffManagedAdminMixin:
    """Users & Groups is a self-service admin request granted personally
    by whichever admin is asked (see the Dashboard's Policies/Help tabs) —
    not restricted to the HR/general (is_superuser) admin the way Django's
    default per-model Permission objects would otherwise require. Any
    active is_staff account, department-scoped or not, can view/add/change
    accounts and groups here — the same is_staff-is-the-whole-boundary
    principle ExpenseReportAdmin already uses (see accounts/decorators.py)."""

    @staff_permission
    def has_module_permission(self, request):
        ...

    @staff_permission
    def has_view_permission(self, request, obj=None):
        ...

    @staff_permission
    def has_add_permission(self, request):
        ...

    @staff_permission
    def has_change_permission(self, request, obj=None):
        ...

    @staff_permission
    def has_delete_permission(self, request, obj=None):
        ...


@admin.register(User)
class UserAdmin(StaffManagedAdminMixin, BaseUserAdmin):
    """Adds the company fields (employee_number, department,
    supervised_department) to Django's stock user admin, and auto-assigns
    an employee_number for any account created here directly (mirroring
    SignUpForm.save() for the public signup path)."""

    list_display = (
        "email",
        "employee_number",
        "first_name",
        "department",
        "supervised_department",
        "is_staff",
        "is_active",
    )
    list_filter = ("department", "supervised_department", "is_staff", "is_active")
    search_fields = ("email", "first_name", "department", "employee_number")
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Company", {"fields": ("employee_number", "department", "supervised_department")}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (("Company", {"fields": ("department",)}),)
    readonly_fields = ("employee_number",)

    def save_model(self, request, obj, form, change):
        if not obj.employee_number:
            obj.employee_number = generate_employee_number()
        super().save_model(request, obj, form, change)


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(StaffManagedAdminMixin, BaseGroupAdmin):
    """Re-registered only to apply StaffManagedAdminMixin — Django's Group
    model otherwise requires the same superuser-only default permissions
    UserAdmin did before this change."""


@admin.register(LoginEvent)
class LoginEventAdmin(admin.ModelAdmin):
    """Read-only session/login trail for the admin's security and
    traceability view. Nothing here is editable — it's an audit record."""

    list_display = ("email_attempted", "user", "success", "ip_address", "created_at")
    list_filter = ("success",)
    search_fields = ("email_attempted", "ip_address")
    readonly_fields = ("user", "email_attempted", "success", "ip_address", "user_agent", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
