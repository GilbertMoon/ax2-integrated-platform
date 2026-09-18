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


class Category:
    """LMS 쪽에서 만드는 알림의 category 값.

    Core `Notification.Category`(TextChoices)는 건드릴 수 없고, choices는
    DB 레벨로 강제되지 않는 CharField라 새 값을 그냥 써도 저장/조회엔 문제없다
    (Core 관리자 화면에서 라벨이 안 예쁘게 나올 수 있다는 것만 트레이드오프).
    """

    ASSIGNMENT_GRADED = "LMS_ASSIGNMENT_GRADED"
    ASSIGNMENT_CREATED = "LMS_ASSIGNMENT_CREATED"
    LESSON_ADDED = "LMS_LESSON_ADDED"
    TEAM_SUBMITTED = "LMS_TEAM_SUBMITTED"


def notify(*, user_id, category, title, message="", link=""):
    """학생 한 명에게 LMS 알림 하나 생성. link는 항상 "/lms/"로 시작해야 벨에 잡힌다."""
    from notifications.models import Notification

    Notification.objects.create(
        recipient_id=user_id,
        category=category,
        title=title,
        message=message,
        link=link,
    )


def notify_many(*, user_ids, category, title, message="", link=""):
    for user_id in user_ids:
        notify(user_id=user_id, category=category, title=title, message=message, link=link)


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
