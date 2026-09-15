import uuid

from django.conf import settings
from django.core.files.storage import storages
from django.db import models


def report_storage():
    return storages["bug_reports"]


def screenshot_path(instance, filename):
    return f"screenshots/{uuid.uuid4().hex}.{filename.rsplit('.', 1)[-1].lower()}"


class BugReport(models.Model):
    class Status(models.TextChoices):
        OPEN = "open", "접수 완료"
        RESOLVED = "resolved", "해결 완료"

    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    title = models.CharField("제목", max_length=200)
    description = models.TextField("오류 내용")
    page_url = models.CharField("발생 페이지", max_length=1000, blank=True)
    screenshot = models.ImageField(
        "캡처 이미지", storage=report_storage, upload_to=screenshot_path, blank=True
    )
    status = models.CharField(
        "처리 상태", max_length=20, choices=Status.choices, default=Status.OPEN
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="handled_bug_reports",
        blank=True,
    )
    created_at = models.DateTimeField("신고일", auto_now_add=True)
    updated_at = models.DateTimeField("수정일", auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]

    def __str__(self):
        return self.title
