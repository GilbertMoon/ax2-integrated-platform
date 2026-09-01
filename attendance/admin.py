from django.contrib import admin

from accounts.admin_permissions import OperationsAdminMixin
from attendance.models import AttendanceRecord


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(OperationsAdminMixin, admin.ModelAdmin):
    list_display = ("date", "user", "status", "checked_by_face_recognition", "updated_at")
    list_filter = ("status", "checked_by_face_recognition")
    search_fields = ("user__email", "user__first_name")
    autocomplete_fields = ("user",)
    date_hierarchy = "date"
