from django.contrib import admin

from accounts.admin_permissions import OperationsReadOnlyAdminMixin
from notifications.models import Notification, SlackIdentity


@admin.register(Notification)
class NotificationAdmin(OperationsReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = ("recipient", "category", "title", "created_at", "read_at")
    list_filter = ("category",)
    search_fields = ("title", "message", "recipient__email")
    readonly_fields = ("created_at",)


@admin.register(SlackIdentity)
class SlackIdentityAdmin(OperationsReadOnlyAdminMixin, admin.ModelAdmin):
    list_display = (
        "slack_display_name",
        "slack_email",
        "user",
        "slack_user_id",
        "is_active",
        "synced_at",
    )
    list_filter = ("is_active",)
    search_fields = ("slack_display_name", "slack_email", "slack_user_id", "user__email")
    readonly_fields = ("synced_at",)
