from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from core.admin import admin_site


User = get_user_model()


class SSOUserAdmin(UserAdmin):
    def has_add_permission(self, request, obj=None):
        return False

    exclude = ("password",)
    fieldsets = (
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )


admin_site.register(User, SSOUserAdmin)
