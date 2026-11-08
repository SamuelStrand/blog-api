
from django.contrib import admin
from django.contrib.auth.admin import (
    GroupAdmin as BaseGroupAdmin,
    UserAdmin as BaseUserAdmin,
)
from django.contrib.auth.models import Group
from django.db.models import Count, QuerySet
from django.http import HttpRequest

from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter
from unfold.decorators import display
from unfold.forms import AdminPasswordChangeForm

from apps.auths.forms import (
    CustomUserChangeForm,
    CustomUserCreationForm,
)
from apps.auths.models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    """CustomUser model admin configuration class."""

    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = (
        "user_header",
        "active_label",
        "staff_label",
        "posts_count",
    )
    list_display_links = ("user_header",)
    list_filter = (
        ("is_active", BooleanRadioFilter),
        ("is_staff", BooleanRadioFilter),
    )
    list_filter_submit = True

    search_fields = (
        "email",
        "first_name",
        "last_name",
    )
    ordering = ("email",)
    list_per_page = 20

    actions = (
        "activate_users",
        "deactivate_users",
    )

    readonly_fields = ("last_login",)
    filter_horizontal = (
        "groups",
        "user_permissions",
    )

    fieldsets = (
        (
            "Personal info",
            {
                "classes": ("tab",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password",
                ),
            },
        ),
        (
            "Permissions",
            {
                "classes": ("tab",),
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important dates",
            {
                "classes": ("tab",),
                "fields": ("last_login",),
            },
        ),
    )

    add_fieldsets = (
        (
            "Create user",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet:
        """Annotate users with number of posts."""

        return (
            super()
            .get_queryset(request)
            .annotate(posts_total=Count("post"))
        )

    @display(description="User", header=True)
    def user_header(self, obj: CustomUser) -> tuple:
        """Return user name, email and initials."""

        full_name: str = (
            f"{obj.first_name} {obj.last_name}".strip()
        )

        initials: str = "".join(
            name[0].upper()
            for name in full_name.split()
        )

        return (
            full_name or obj.email,
            obj.email,
            initials or "U",
        )

    @display(
        description="Active",
        ordering="is_active",
        label={
            True: "success",
            False: "danger",
        },
    )
    def active_label(self, obj: CustomUser) -> tuple:
        """Return colored active status."""

        return (
            obj.is_active,
            "Active" if obj.is_active else "Inactive",
        )

    @display(
        description="Staff",
        ordering="is_staff",
        label={
            True: "info",
            False: "warning",
        },
    )
    def staff_label(self, obj: CustomUser) -> tuple:
        """Return colored staff status."""

        return (
            obj.is_staff,
            "Staff" if obj.is_staff else "Regular",
        )

    @display(description="Posts", ordering="posts_total")
    def posts_count(self, obj: CustomUser) -> int:
        """Return number of authored posts."""

        return obj.posts_total

    @admin.action(description="Activate selected users")
    def activate_users(
        self,
        request: HttpRequest,
        queryset: QuerySet,
    ) -> None:
        """Activate selected users."""

        updated: int = queryset.update(is_active=True)

        self.message_user(
            request,
            f"{updated} users activated.",
        )

    @admin.action(description="Deactivate selected users")
    def deactivate_users(
        self,
        request: HttpRequest,
        queryset: QuerySet,
    ) -> None:
        """Deactivate selected users except superusers."""

        updated: int = queryset.exclude(
            is_superuser=True
        ).update(is_active=False)

        self.message_user(
            request,
            f"{updated} users deactivated.",
        )


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    """Group model admin with Unfold styling."""

    pass
