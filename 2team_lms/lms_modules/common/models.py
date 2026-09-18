"""apps/common/models.py — 공통 담당 전담.

LMS 자체 알림 전용 테이블. Core `notifications.Notification`과 완전히 분리한다 —
그 테이블을 같이 쓰면 Core 자체 알림 벨(필터 없이 recipient의 전체 알림을 보여줌)에
LMS 알림까지 섞여 보이는 문제가 있었다. 테이블을 통째로 떼어내면 그 문제 자체가
성립하지 않는다 (Core 쪽에서 이 테이블을 볼 일이 없다).
"""

from django.db import models


class LmsNotification(models.Model):
    recipient_id = models.IntegerField(db_index=True, help_text="accounts_user.id 참조, FK 아님")
    category = models.CharField(max_length=50)
    title = models.CharField(max_length=200)
    message = models.CharField(max_length=500, blank=True)
    link = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "lms_notification"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["recipient_id", "read_at"], name="lms_notif_recipient_read_idx"),
        ]

    def __str__(self):
        return f"{self.recipient_id} - {self.title}"
