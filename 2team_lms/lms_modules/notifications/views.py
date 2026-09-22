"""LMS 알림 벨/패널 API — Core notifications/views.py 의 summary/read/delete 계열과
동일한 모양으로 응답하되, services.py 를 통해 LMS 알림(link가 "/lms/"로 시작)만 다룬다.
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from . import services


def _serialize(notification):
    return {
        "id": notification.pk,
        "category": notification.category,
        "title": notification.title,
        "message": notification.message,
        "link": notification.link,
        "created_at": notification.created_at.isoformat(),
        "is_read": notification.read_at is not None,
    }


@login_required
def summary(request):
    items = services.recent_notifications(request.user)
    return JsonResponse({
        "unread_count": services.unread_count(request.user),
        "items": [_serialize(item) for item in items],
    })


@login_required
@require_POST
def mark_read_view(request, notification_id):
    services.mark_read(user=request.user, notification_id=notification_id)
    return JsonResponse({"unread_count": services.unread_count(request.user)})


@login_required
@require_POST
def open_view(request, notification_id):
    """알림 클릭 시 서버에서 대상 존재 여부를 먼저 확인한다.
    삭제된 과제/강의라면 알림을 지우고 실패로 응답 — 클라이언트는 이동하지 않는다."""
    result = services.open_notification(user=request.user, notification_id=notification_id)
    status = 200 if result["ok"] else 404
    return JsonResponse(
        {**result, "unread_count": services.unread_count(request.user)}, status=status
    )


@login_required
@require_POST
def mark_all_read_view(request):
    services.mark_all_read(request.user)
    return JsonResponse({"unread_count": 0})


@login_required
@require_POST
def delete_view(request, notification_id):
    services.delete_notification(user=request.user, notification_id=notification_id)
    return JsonResponse({"unread_count": services.unread_count(request.user)})


@login_required
@require_POST
def delete_all_view(request):
    services.delete_all_notifications(request.user)
    return JsonResponse({"unread_count": 0})
