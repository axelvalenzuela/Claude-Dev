from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("email", "first_name", "department", "is_staff", "is_active")
    list_filter = ("department", "is_staff", "is_active")
    search_fields = ("email", "first_name", "department")
    fieldsets = BaseUserAdmin.fieldsets + (("Empresa", {"fields": ("department",)}),)
    add_fieldsets = BaseUserAdmin.add_fieldsets + (("Empresa", {"fields": ("department",)}),)
