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


class FaceEmbedding(models.Model):
    """
    학생 profile_image로부터 미리 계산해둔 "얼굴 특징 벡터"를 저장한다.
    출석 체크할 때마다 매번 DeepFace로 새로 계산하지 않고,
    이미 계산된 값을 재사용해서 속도를 크게 높인다.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="face_embedding",
        verbose_name=_("사용자"),
    )
    vector = models.JSONField(
        _("특징 벡터"), help_text=_("숫자 목록 형태로 저장 (예: [0.12, -0.4, ...])")
    )
    source_image_name = models.CharField(
        _("계산에 사용한 사진 파일명"),
        max_length=255,
        blank=True,
        default="",
        help_text=_("profile_image가 바뀌었는지 확인용"),
    )
    created_at = models.DateTimeField(_("계산 일시"), auto_now_add=True)
    updated_at = models.DateTimeField(_("갱신 일시"), auto_now=True)

    class Meta:
        verbose_name = _("얼굴 특징 벡터")
        verbose_name_plural = _("얼굴 특징 벡터 목록")

    def __str__(self):
        name = self.user.first_name or self.user.email
        return f"{name}의 얼굴 벡터"
