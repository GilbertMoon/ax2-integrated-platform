import os

import requests
from django.db import transaction
from django.utils import timezone
from dotenv import load_dotenv

from accounts.models import User
from notifications.models import SlackIdentity

load_dotenv()
SLACK_API_URL = "https://slack.com/api"


def _format_message(*, title, message="", link=""):
    text = f"*{title}*"
    if message:
        text += f"\n{message}"
    if link:
        text += f"\n<{link}|상세 보기>"
    return text


def _slack_headers():
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        return None
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json; charset=utf-8",
    }


def _slack_post(endpoint, *, headers, payload):
    response = requests.post(
        f"{SLACK_API_URL}/{endpoint}",
        headers=headers,
        json=payload,
        timeout=5,
    )
    response.raise_for_status()
    data = response.json()
    if not data.get("ok"):
        return None
    return data


def send_slack_message(*, title, message="", link=""):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return False
    try:
        response = requests.post(
            webhook_url,
            json={"text": _format_message(title=title, message=message, link=link)},
            timeout=5,
        )
        response.raise_for_status()
    except requests.RequestException:
        return False
    return True


def send_slack_dm(*, user=None, slack_user_id=None, title, message="", link=""):
    """Send a DM using a project User, with Slack ID as a legacy fallback."""
    if user is not None:
        slack_identity = getattr(user, "slack_identity", None)
        slack_user_id = slack_identity.slack_user_id if slack_identity and slack_identity.is_active else None

    headers = _slack_headers()
    if not headers or not slack_user_id:
        return False

    try:
        open_data = _slack_post(
            "conversations.open", headers=headers, payload={"users": slack_user_id}
        )
        if not open_data:
            return False
        channel_id = open_data["channel"]["id"]
        message_data = _slack_post(
            "chat.postMessage",
            headers=headers,
            payload={
                "channel": channel_id,
                "text": _format_message(title=title, message=message, link=link),
            },
        )
        return message_data is not None
    except (requests.RequestException, ValueError, KeyError, TypeError):
        return False


def send_slack_dm_ax(ax_user_id, title, message="", link=""):
    """Send a Slack DM using the project's User ID."""
    user = User.objects.filter(pk=ax_user_id, is_active=True).first()
    if not user:
        return False
    return send_slack_dm(user=user, title=title, message=message, link=link)


def fetch_slack_users():
    """Fetch all non-bot Slack workspace members, following cursor pagination."""
    headers = _slack_headers()
    if not headers:
        raise RuntimeError("SLACK_BOT_TOKEN이 설정되지 않았습니다.")

    members = []
    cursor = ""
    try:
        while True:
            payload = {"limit": 200}
            if cursor:
                payload["cursor"] = cursor
            data = _slack_post("users.list", headers=headers, payload=payload)
            if not data:
                raise RuntimeError("Slack 사용자 목록을 가져오지 못했습니다.")

            for member in data.get("members", []):
                if member.get("is_bot") or member.get("id", "").startswith("USLACKBOT"):
                    continue
                profile = member.get("profile") or {}
                members.append(
                    {
                        "slack_user_id": member.get("id", ""),
                        "email": (profile.get("email") or "").strip().lower(),
                        "display_name": (
                            profile.get("display_name")
                            or profile.get("real_name")
                            or member.get("real_name")
                            or ""
                        ).strip(),
                        "is_active": not member.get("deleted", False),
                    }
                )

            cursor = (data.get("response_metadata") or {}).get("next_cursor", "").strip()
            if not cursor:
                return members
    except (requests.RequestException, ValueError, TypeError) as exc:
        raise RuntimeError("Slack 사용자 목록 조회 중 오류가 발생했습니다.") from exc


def sync_slack_users():
    """Sync all Slack members and auto-link project users by email."""
    slack_users = fetch_slack_users()
    project_users = {
        user.email.strip().lower(): user
        for user in User.objects.filter(is_active=True).exclude(email="")
    }
    linked = 0
    unmatched = 0
    slack_ids = set()

    with transaction.atomic():
        for item in slack_users:
            slack_user_id = item["slack_user_id"]
            if not slack_user_id:
                continue
            slack_ids.add(slack_user_id)
            user = project_users.get(item["email"])
            identity, _ = SlackIdentity.objects.get_or_create(
                slack_user_id=slack_user_id,
                defaults={"is_active": item["is_active"]},
            )

            identity.slack_email = item["email"]
            identity.slack_display_name = item["display_name"]
            identity.is_active = item["is_active"]

            if user:
                SlackIdentity.objects.filter(user=user).exclude(pk=identity.pk).update(user=None)
                identity.user = user
                linked += 1
            elif identity.user_id is None:
                unmatched += 1

            identity.save()

        SlackIdentity.objects.exclude(slack_user_id__in=slack_ids).update(is_active=False)

    return {"total": len(slack_users), "linked": linked, "unmatched": unmatched, "synced_at": timezone.now()}


def link_slack_user(*, user, slack_user_id):
    """Manually connect one project User to one synced Slack member."""
    if not user or not slack_user_id:
        raise ValueError("사용자와 Slack Member ID가 필요합니다.")

    identity = SlackIdentity.objects.filter(slack_user_id=slack_user_id, is_active=True).first()
    if not identity:
        raise ValueError("먼저 Slack 사용자 동기화를 실행해주세요.")
    if identity.user_id and identity.user_id != user.pk:
        raise ValueError("해당 Slack 사용자는 이미 다른 프로젝트 사용자와 연결되어 있습니다.")

    with transaction.atomic():
        SlackIdentity.objects.filter(user=user).exclude(pk=identity.pk).update(user=None)
        identity.user = user
        identity.save(update_fields=["user", "synced_at"])
        return identity
