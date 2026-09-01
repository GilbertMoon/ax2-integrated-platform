# accounts/models.py의 User 모델 컨벤션(TextChoices + gettext_lazy)을 그대로 따른다.

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class AttendanceRecord(models.Model):
    """
    근태(출결) 기록. accounts_user.id(Master ID)를 참조한다.
    teams 앱의 RoundParticipant와는 무관 - 근태는 항상 User 기준이다.
    """

    class Status(models.TextChoices):
        PRESENT = "present", _("출석")
        LATE = "late", _("지각")
        ABSENT = "absent", _("결석")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="attendance_records",
        verbose_name=_("사용자"),
    )
    date = models.DateField(_("근태 일자"))
    status = models.CharField(_("상태"), max_length=20, choices=Status.choices)
    checked_by_face_recognition = models.BooleanField(_("얼굴인식 자동 기록 여부"), default=False)
    memo = models.CharField(_("메모"), max_length=200, blank=True, default="")

    created_at = models.DateTimeField(_("생성 일시"), auto_now_add=True)
    updated_at = models.DateTimeField(_("수정 일시"), auto_now=True)

    class Meta:
        verbose_name = _("근태 기록")
        verbose_name_plural = _("근태 기록 목록")
        constraints = [
            models.UniqueConstraint(fields=("user", "date"), name="attendance_user_date_unique"),
        ]
        ordering = ["-date"]

    def __str__(self):
        name = self.user.first_name if self.user.first_name else self.user.email
        return f"{name} / {self.date} / {self.get_status_display()}"
