from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from accounts.models import User
from accounts.permissions import is_operations_user
from notifications.models import SlackIdentity
from notifications.services import (
    delete_all_notifications,
    delete_notification,
    link_slack_user,
    mark_all_read,
    mark_read,
    recent_notifications,
    send_slack_to_users,
    sync_slack_users,
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
    return JsonResponse({"unread_count": unread_count(request.user), "items": [_serialize(item) for item in items]})


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


def unread_count(user):
    from notifications.services import unread_count as get_unread_count
    return get_unread_count(user)


def _require_operations(request):
    if not is_operations_user(request.user):
        raise PermissionDenied


@login_required
def slack_management(request):
    _require_operations(request)
    project_users = list(
        User.objects.filter(is_active=True).select_related("slack_identity").order_by("email")
    )
    slack_users = list(SlackIdentity.objects.filter(is_active=True).select_related("user"))
    return render(request, "notifications/slack_management.html", {"project_users": project_users, "slack_users": slack_users})


@login_required
@require_POST
def slack_sync_view(request):
    _require_operations(request)
    try:
        result = sync_slack_users()
    except RuntimeError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
    return JsonResponse({"ok": True, **result})


@login_required
@require_POST
def slack_link_view(request):
    _require_operations(request)
    user = User.objects.filter(pk=request.POST.get("user_id"), is_active=True).first()
    if not user:
        return JsonResponse({"ok": False, "error": "프로젝트 사용자를 찾을 수 없습니다."}, status=400)
    try:
        identity = link_slack_user(user=user, slack_user_id=(request.POST.get("slack_user_id") or "").strip())
    except ValueError as exc:
        return JsonResponse({"ok": False, "error": str(exc)}, status=400)
    return JsonResponse({"ok": True, "slack_user_id": identity.slack_user_id})


@login_required
def slack_send(request):
    _require_operations(request)
    slack_users = list(SlackIdentity.objects.filter(is_active=True).select_related("user").order_by("slack_display_name", "slack_user_id"))
    teams = []
    if request.method == "POST":
        target_type = request.POST.get("target_type", "individual")
        title = (request.POST.get("title") or "").strip()
        message = (request.POST.get("message") or "").strip()
        link = (request.POST.get("link") or "").strip()

        if not title:
            messages.error(request, "메시지 제목을 입력해주세요.")
        elif target_type == "individual":
            identity = SlackIdentity.objects.filter(pk=request.POST.get("slack_identity_id"), is_active=True).first()
            if not identity:
                messages.error(request, "Slack 사용자를 선택해주세요.")
            else:
                from notifications.slack import send_slack_dm
                if send_slack_dm(slack_user_id=identity.slack_user_id, title=title, message=message, link=link):
                    messages.success(request, f"{identity.slack_display_name or identity.slack_user_id}님에게 Slack DM을 보냈습니다.")
                else:
                    messages.error(request, "Slack DM 전송에 실패했습니다.")
        elif target_type == "team":
            from teams.models import Team
            team = Team.objects.filter(pk=request.POST.get("team_id")).first()
            if not team:
                messages.error(request, "팀을 선택해주세요.")
            else:
                users = User.objects.filter(is_active=True, slack_identity__is_active=True, round_participations__team_membership__team=team).select_related("slack_identity").distinct()
                results = send_slack_to_users(users, title=title, message=message, link=link)
                success_count = sum(ok for _, ok in results)
                if success_count:
                    messages.success(request, f"{success_count}명에게 Slack DM을 보냈습니다.")
                else:
                    messages.error(request, "연결된 Slack 사용자가 없어 전송하지 못했습니다.")
        elif target_type == "all":
            from notifications.slack import send_slack_dm
            results = [send_slack_dm(slack_user_id=identity.slack_user_id, title=title, message=message, link=link) for identity in slack_users]
            success_count = sum(results)
            if success_count:
                messages.success(request, f"{success_count}명에게 Slack DM을 보냈습니다.")
            else:
                messages.error(request, "Slack DM 전송에 실패했습니다.")
        else:
            messages.error(request, "올바른 발송 대상을 선택해주세요.")
        return redirect("notifications:slack-send")

    from teams.models import Team
    teams = list(Team.objects.select_related("round").order_by("-round__created_at", "team_number"))
    return render(request, "notifications/slack_send.html", {"slack_users": slack_users, "teams": teams})
