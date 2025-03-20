from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for the custom User model."""
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "email", "phone_number", "job_title", "organization")}),
        (_("Preferences"), {"fields": ("use_dark_mode",)}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined", "created_at", "updated_at")}),
    )
    readonly_fields = ["created_at", "updated_at"]
    list_display = ["username", "email", "first_name", "last_name", "is_staff", "organization"]
    search_fields = ["username", "first_name", "last_name", "email", "organization"]
    list_filter = ["is_staff", "is_superuser", "is_active", "use_dark_mode"]