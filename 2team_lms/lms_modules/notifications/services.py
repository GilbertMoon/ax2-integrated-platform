"""LMS 알림 — Core `notifications.Notification` 을 원본으로 하되 LMS 것만 걸러서 본다.

Core와 LMS는 같은 프로세스·같은 `default` DB에서 알림 테이블 하나를 공유한다
(Core 자체 알림 카테고리는 전부 평가시스템 전용: 라운드/팀/결과 등). LMS 쪽에서
만드는 알림은 항상 `link` 를 "/lms/" 로 시작하게 채워서 남기고, 조회할 때 그
prefix 로 필터링해 Core 알림과 섞이지 않게 한다. Core 모델(notifications/models.py)
자체는 건드리지 않는다 — 이 모듈 밖에서는 절대 import 하지 말 것.

지연 import: 앱 레지스트리 준비 전 순환참조를 피하기 위함 — notices_client와 동일 패턴.
"""

from django.utils import timezone

LMS_LINK_PREFIX = "/lms/"


def _lms_notifications(user):
    from notifications.models import Notification

    return Notification.objects.filter(recipient=user, link__startswith=LMS_LINK_PREFIX)


def unread_count(user):
    return _lms_notifications(user).filter(read_at__isnull=True).count()


def recent_notifications(user, limit=30):
    return list(_lms_notifications(user)[:limit])


def mark_read(*, user, notification_id):
    _lms_notifications(user).filter(pk=notification_id, read_at__isnull=True).update(
        read_at=timezone.now()
    )


def mark_all_read(user):
    _lms_notifications(user).filter(read_at__isnull=True).update(read_at=timezone.now())


def delete_notification(*, user, notification_id):
    _lms_notifications(user).filter(pk=notification_id).delete()


def delete_all_notifications(user):
    _lms_notifications(user).delete()
