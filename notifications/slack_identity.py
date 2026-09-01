from dataclasses import dataclass
from typing import Iterable

from django.contrib.auth import get_user_model
from django.db import models


User = get_user_model()


class SlackIdentity(models.Model):
    """Links one project user to one Slack workspace member."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="slack_identity",
    )
    slack_user_id = models.CharField(max_length=32, unique=True)
    slack_email = models.EmailField(blank=True, default="")
    slack_display_name = models.CharField(max_length=255, blank=True, default="")
    is_active = models.BooleanField(default=True)
    synced_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Slack 사용자 연동"
        verbose_name_plural = "Slack 사용자 연동 목록"

    def __str__(self):
        return f"{self.user} -> {self.slack_user_id}"


@dataclass(frozen=True)
class SlackUserCandidate:
    slack_user_id: str
    email: str
    display_name: str
    is_active: bool = True


def match_slack_users_to_users(
    slack_users: Iterable[SlackUserCandidate],
):
    """Return safe automatic matches based on canonical project email."""
    users_by_email = {
        user.email.strip().lower(): user
        for user in User.objects.filter(is_active=True).exclude(email="")
    }

    matches = []
    for slack_user in slack_users:
        email = slack_user.email.strip().lower()
        if not email:
            continue
        user = users_by_email.get(email)
        if user:
            matches.append((user, slack_user))

    return matches
