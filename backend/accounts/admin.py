from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Extends the default UserAdmin to surface role and manager fields."""

    list_display = ("username", "email", "get_full_name", "role", "manager", "is_active")
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
    autocomplete_fields = ("manager",)

    # Inject role and manager into the existing fieldsets
    fieldsets = BaseUserAdmin.fieldsets + (
        (
            _("Role & Hierarchy"),
            {"fields": ("role", "manager")},
        ),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (
            _("Role & Hierarchy"),
            {"fields": ("role", "manager")},
        ),
    )