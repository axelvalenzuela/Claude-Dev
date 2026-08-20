from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import LoginEvent, User, generate_employee_number


@admin.register(User)
class UserAdmin(BaseUserAdmin):
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
