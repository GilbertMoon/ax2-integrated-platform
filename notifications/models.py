from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Category(models.TextChoices):
        NOTICE = "NOTICE", "공지"
        ROUND_CREATED = "ROUND_CREATED", "새 회차"
        ROUND_STARTED = "ROUND_STARTED", "평가 시작"
        TEAM_CREATED = "TEAM_CREATED", "새 팀"
        ROUND_COMPLETED = "ROUND_COMPLETED", "평가 종료"
        RESULTS_PUBLISHED = "RESULTS_PUBLISHED", "결과 공개"
        SUBMISSION_REMINDER = "SUBMISSION_REMINDER", "제출 안내"
        PARTICIPANT_COMPLETED = "PARTICIPANT_COMPLETED", "제출 완료"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="수신자",
    )
    category = models.CharField("종류", max_length=30, choices=Category.choices)
    title = models.CharField("제목", max_length=200)
    message = models.CharField("내용", max_length=300, blank=True)
    link = models.CharField("이동 경로", max_length=300, blank=True)
    created_at = models.DateTimeField("생성일", auto_now_add=True)
    read_at = models.DateTimeField("읽은 시각", null=True, blank=True)

    class Meta:
        verbose_name = "알림"
        verbose_name_plural = "알림 목록"
        ordering = ("-created_at", "-id")
        indexes = [models.Index(fields=("recipient", "read_at"))]

    def __str__(self):
        return f"{self.recipient_id}:{self.category}:{self.title}"


class SlackIdentity(models.Model):
    """Connects one project User to one Slack workspace member."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="slack_identity",
        verbose_name="프로젝트 사용자",
    )
    slack_user_id = models.CharField("Slack Member ID", max_length=32, unique=True)
    slack_email = models.EmailField("Slack 이메일", blank=True, default="")
    slack_display_name = models.CharField("Slack 표시 이름", max_length=255, blank=True, default="")
    is_active = models.BooleanField("Slack 활성 사용자", default=True)
    synced_at = models.DateTimeField("동기화 일시", auto_now=True)

    class Meta:
        verbose_name = "Slack 사용자 연동"
        verbose_name_plural = "Slack 사용자 연동 목록"
        ordering = ("user__email",)

    def __str__(self):
        return f"{self.user} → {self.slack_display_name or self.slack_user_id}"
