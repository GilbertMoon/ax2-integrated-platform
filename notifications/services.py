from django.db import transaction
from django.utils import timezone

from accounts.models import User
from notifications.models import Notification, SlackIdentity
from notifications.slack import fetch_slack_users, send_slack_dm
from notifications.slack import link_slack_user as link_slack_identity

# 메일 템플릿이 있는 알림 종류. 마이페이지의 수신 설정도 이 목록으로 그린다.
EMAIL_CAPABLE_CATEGORIES = (
    Notification.Category.NOTICE,
    Notification.Category.ROUND_STARTED,
    Notification.Category.SUBMISSION_REMINDER,
    Notification.Category.RESULTS_PUBLISHED,
)


def announce(users, *, category, title, message="", link="", email_sender=None):
    recipients = list(users)
    notify_users(recipients, category=category, title=title, message=message, link=link)
    if email_sender is None:
        return []
    wanted = [user for user in recipients if user.wants_email(category)]
    if wanted:
        email_sender(wanted)
    return wanted


def notify_users(users, *, category, title, message="", link=""):
    user_ids = {user.pk for user in users}
    Notification.objects.bulk_create(
        Notification(
            recipient_id=user_id,
            category=category,
            title=title,
            message=message,
            link=link,
        )
        for user_id in user_ids
    )


def unread_count(user):
    return Notification.objects.filter(recipient=user, read_at__isnull=True).count()


def recent_notifications(user, limit=30):
    return Notification.objects.filter(recipient=user)[:limit]


def mark_read(*, user, notification_id):
    Notification.objects.filter(recipient=user, pk=notification_id, read_at__isnull=True).update(
        read_at=timezone.now()
    )


def mark_all_read(user):
    Notification.objects.filter(recipient=user, read_at__isnull=True).update(read_at=timezone.now())


def delete_notification(*, user, notification_id):
    Notification.objects.filter(recipient=user, pk=notification_id).delete()


def delete_all_notifications(user):
    Notification.objects.filter(recipient=user).delete()


def sync_slack_users():
    """Import all Slack members and auto-link project users by email."""
    slack_users = fetch_slack_users()
    project_users = {
        user.email.strip().lower(): user
        for user in User.objects.filter(is_active=True).exclude(email="")
    }
    linked = 0
    unmatched = 0
    slack_ids = set()

    with transaction.atomic():
        for slack_user in slack_users:
            slack_user_id = slack_user["slack_user_id"]
            if not slack_user_id:
                continue
            slack_ids.add(slack_user_id)
            user = project_users.get(slack_user["email"])

            if user:
                SlackIdentity.objects.filter(user=user).exclude(slack_user_id=slack_user_id).update(
                    user=None
                )
                SlackIdentity.objects.update_or_create(
                    slack_user_id=slack_user_id,
                    defaults={
                        "user": user,
                        "slack_email": slack_user["email"],
                        "slack_display_name": slack_user["display_name"],
                        "is_active": slack_user["is_active"],
                    },
                )
                linked += 1
            else:
                # 프로젝트에 아직 가입하지 않은 Slack 사용자도 저장한다.
                # 그래야 개인/전체 Slack 발송에서 선택할 수 있다.
                SlackIdentity.objects.update_or_create(
                    slack_user_id=slack_user_id,
                    defaults={
                        "user": None,
                        "slack_email": slack_user["email"],
                        "slack_display_name": slack_user["display_name"],
                        "is_active": slack_user["is_active"],
                    },
                )
                unmatched += 1

        SlackIdentity.objects.exclude(slack_user_id__in=slack_ids).update(is_active=False)

    return {"total": len(slack_users), "linked": linked, "unmatched": unmatched}


def link_slack_user(*, user, slack_user_id):
    """Manually link one project User to one Slack member."""
    return link_slack_identity(user=user, slack_user_id=slack_user_id)


def send_user_slack_dm(*, user, title, message="", link=""):
    """Send a DM to a project User through their linked Slack identity."""
    return send_slack_dm(user=user, title=title, message=message, link=link)


def send_slack_to_users(users, *, title, message="", link=""):
    """Send the same Slack DM to each project User with a linked Slack identity."""
    results = []
    for user in users:
        results.append(
            (user, send_user_slack_dm(user=user, title=title, message=message, link=link))
        )
    return results
