from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.permissions import is_operations_user
from notifications.services import (
    delete_all_notifications,
    delete_notification,
    link_slack_user,
    mark_all_read,
    mark_read,
    recent_notifications,
    sync_slack_users,
    unread_count,
)


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
    items = list(recent_notifications(request.user))
    return JsonResponse(
        {
            "unread_count": unread_count(request.user),
            "items": [_serialize(item) for item in items],
        }
    )


@login_required
@require_POST
def mark_read_view(request, notification_id):
    mark_read(user=request.user, notification_id=notification_id)
    return JsonResponse({"unread_count": unread_count(request.user)})


@login_required
@require_POST
def mark_all_read_view(request):
    mark_all_read(request.user)
    return JsonResponse({"unread_count": 0})


@login_required
@require_POST
def delete_view(request, notification_id):
    delete_notification(user=request.user, notification_id=notification_id)
    return JsonResponse({"unread_count": unread_count(request.user)})


@login_required
@require_POST
def delete_all_view(request):
    delete_all_notifications(request.user)
    return JsonResponse({"unread_count": 0})


def _require_operations(request):
    if not is_operations_user(request.user):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied


@login_required
def slack_management(request):
    _require_operations(request)
    users = User.objects.filter(is_active=True).select_related("slack_identity").order_by("email")
    slack_identities = {identity.user_id: identity for identity in users if hasattr(identity, "slack_identity")}
    users_with_identity = []
    for user in users:
        users_with_identity.append((user, slack_identities.get(user.pk)))
    return render(request, "notifications/slack_management.html", {"users": users_with_identity})


@login_required
@require_POST
def slack_sync_view(request):
    _require_operations(request)
    try:
        result = sync_slack_users()
    except RuntimeError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
    return JsonResponse({
        "ok": True,
        "total": result["total"],
        "linked": result["linked"],
        "unmatched": result["unmatched"],
    })


@login_required
@require_POST
def slack_link_view(request):
    _require_operations(request)
    user_id = request.POST.get("user_id")
    slack_user_id = (request.POST.get("slack_user_id") or "").strip()
    user = User.objects.filter(pk=user_id, is_active=True).first()
    if not user:
        return JsonResponse({"ok": False, "error": "프로젝트 사용자를 찾을 수 없습니다."}, status=400)
    try:
        identity = link_slack_user(user=user, slack_user_id=slack_user_id)
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
    return JsonResponse({"ok": True, "slack_user_id": identity.slack_user_id})
