"""LMS 알림 — Core notifications.Notification과 완전히 분리된 전용 테이블(LmsNotification)만 쓴다.

Core 자체 알림 벨(notifications.services.recent_notifications)은 recipient의
전체 알림을 필터 없이 보여주기 때문에, 한때 Core Notification 테이블을 같이 썼을 때
LMS 알림이 Core 화면에도 그대로 섞여 보이는 문제가 있었다. 테이블 자체를
lms_modules.common.models.LmsNotification 으로 떼어내서 그 문제를 원천적으로 없앤다
(Core notices 앱을 "원본으로 읽기만" 하는 notices_client와는 반대 방향 —
여기는 우리가 "쓰는" 쪽이라 공유 테이블을 쓸 수 없다).
"""

from django.utils import timezone

from lms_modules.common.models import LmsNotification


class Category:
    """LMS 쪽에서 만드는 알림의 category 값. 자유 문자열 — 우리 테이블이라 제약 없다."""

    ASSIGNMENT_GRADED = "LMS_ASSIGNMENT_GRADED"
    ASSIGNMENT_CREATED = "LMS_ASSIGNMENT_CREATED"
    LESSON_ADDED = "LMS_LESSON_ADDED"
    TEAM_SUBMITTED = "LMS_TEAM_SUBMITTED"


class TargetType:
    """target_type 값. 알림이 가리키는 대상이 클릭 시점에도 존재하는지 확인하는 용도."""

    ASSIGNMENT = "assignment"
    LESSON = "lesson"
    SUBMISSION = "submission"


def _target_model(target_type):
    from lms_modules.core.models import Assignment, Lesson, Submission

    return {
        TargetType.ASSIGNMENT: Assignment,
        TargetType.LESSON: Lesson,
        TargetType.SUBMISSION: Submission,
    }.get(target_type)


def target_still_exists(notification):
    """알림이 가리키는 대상(과제/강의/제출물)이 아직 있는지. target_type/id가 없는
    옛 알림은 확인할 수 없으니 있는 것으로 간주한다(하위 호환)."""
    if not notification.target_type or notification.target_id is None:
        return True
    model = _target_model(notification.target_type)
    if model is None:
        return True
    return model.objects.filter(pk=notification.target_id).exists()


def notify(*, user_id, category, title, message="", link="", target_type="", target_id=None):
    """학생 한 명에게 LMS 알림 하나 생성."""
    LmsNotification.objects.create(
        recipient_id=user_id,
        category=category,
        title=title,
        message=message,
        link=link,
        target_type=target_type,
        target_id=target_id,
    )


def notify_many(*, user_ids, category, title, message="", link="", target_type="", target_id=None):
    """여러 명에게 알림 생성 — 실제로 존재하는 유저에게만 보낸다.

    accounts_client(get_students/get_team_members 등)가 반환하는 id가 accounts_user와
    100% 일치한다는 보장은 없다 (예: DEV_SKIP_AUTH 개발/테스트 모드의 가짜 fixture id).
    FK가 아니라 존재하지 않아도 저장은 되지만, 아무도 못 볼 유령 알림을 만들 이유는
    없으니 여기서 걸러낸다.
    """
    from accounts.models import User

    valid_ids = set(User.objects.filter(id__in=user_ids).values_list("id", flat=True))
    for user_id in user_ids:
        if user_id in valid_ids:
            notify(
                user_id=user_id, category=category, title=title, message=message,
                link=link, target_type=target_type, target_id=target_id,
            )


def _lms_notifications(user):
    return LmsNotification.objects.filter(recipient_id=user.id)


def unread_count(user):
    return _lms_notifications(user).filter(read_at__isnull=True).count()


def recent_notifications(user, limit=30):
    return list(_lms_notifications(user)[:limit])


def mark_read(*, user, notification_id):
    _lms_notifications(user).filter(pk=notification_id, read_at__isnull=True).update(
        read_at=timezone.now()
    )


def open_notification(*, user, notification_id):
    """알림 클릭 시 호출. 대상이 아직 있으면 읽음 처리하고 이동할 링크를 반환하고,
    삭제된 과제/강의 등이라 대상이 없으면 그 알림 자체를 지우고 실패를 반환한다."""
    notification = _lms_notifications(user).filter(pk=notification_id).first()
    if notification is None:
        return {"ok": False}
    if not target_still_exists(notification):
        notification.delete()
        return {"ok": False}
    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])
    return {"ok": True, "link": notification.link}


def mark_all_read(user):
    _lms_notifications(user).filter(read_at__isnull=True).update(read_at=timezone.now())


def delete_notification(*, user, notification_id):
    _lms_notifications(user).filter(pk=notification_id).delete()


def delete_all_notifications(user):
    _lms_notifications(user).delete()
