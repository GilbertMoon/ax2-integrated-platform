"""Slack 알림.

- `send_slack_message` / `send_slack_dm` / `send_slack_dm_ax` : 저수준 전송 (동기, 실패 시 False).
  어떤 예외도 밖으로 던지지 않는다 — accounts DB 장애로도 호출부가 500 나면 안 된다.
- `notify_channel` / `notify_dm_ax` / `notify_dm_ax_many` : 뷰에서 쓰는 진입점.
  기본은 백그라운드 스레드로 던지고 즉시 반환한다 (요청 사이클을 막지 않음).
  `settings.SLACK_NOTIFY_SYNC=True` 면 동기 실행 (테스트/CLI 용).

큐·워커 없이 스레드로 처리한다. 부트캠프 규모에선 충분하고, 트래픽이 커지면
Celery 등으로 교체 (docs/source-delivery.md known issue).
"""

import logging
import os
import threading

import requests
from django.conf import settings
from django.db import close_old_connections

from notifications.models import SlackIdentity

logger = logging.getLogger(__name__)

SLACK_API_URL = "https://slack.com/api"


def _format_message(*, title, message="", link=""):
    text = f"*{title}*"

    if message:
        text += f"\n{message}"

    if link:
        text += f"\n<{link}|상세 보기>"

    return text


def _safe_send(function, *args, **kwargs):
    try:
        return function(*args, **kwargs)
    except Exception:
        logger.exception("Core Slack notification failed")
        return False


def send_slack_message(*, title, message="", link=""):
    from notifications.slack import send_slack_message as send
    return _safe_send(send, title=title, message=message, link=link)


def send_slack_dm(*, slack_user_id, title, message="", link=""):
    from notifications.slack import send_slack_dm as send
    return _safe_send(send, slack_user_id=slack_user_id, title=title, message=message, link=link)


def send_slack_dm_ax(ax_user_id, title="알림 제목", message="", link=""):
    from notifications.slack import send_slack_dm_ax as send
    return _safe_send(send, ax_user_id, title, message, link)


# ─────────────────────────────────────────────────────────────
# 뷰용 진입점 — 기본 비동기 (요청 사이클을 막지 않음)
# ─────────────────────────────────────────────────────────────
def _dispatch(job):
    """job() 을 백그라운드 스레드에서 실행. SLACK_NOTIFY_SYNC 면 그 자리에서 실행."""

    if getattr(settings, "SLACK_NOTIFY_SYNC", False):
        try:
            job()
        except Exception:  # noqa: BLE001
            logger.exception("slack notify job 실패")
        return

    def _run():
        try:
            job()
        except Exception:  # noqa: BLE001
            logger.exception("slack notify job 실패")
        finally:
            close_old_connections()  # 이 스레드가 연 DB 커넥션 정리

    threading.Thread(target=_run, daemon=True).start()


def active_slack_user_ids(ax_user_ids):
    """주어진 ax_user_id 중 활성 Slack 연동이 있는 것만 (조회 1회, 실패 시 빈 리스트).

    독려 뷰가 "몇 명에게 실제로 보내는지" 를 응답 시점에 알려주기 위해 쓴다 —
    실제 DM(HTTP)은 여전히 백그라운드에서 돈다.
    """
    ids = [uid for uid in ax_user_ids if uid is not None]
    if not ids:
        return []
    try:
        return list(
            SlackIdentity.objects.filter(user_id__in=ids, is_active=True)
            .values_list("user_id", flat=True)
        )
    except Exception:  # noqa: BLE001
        logger.warning("SlackIdentity 일괄 조회 실패", exc_info=True)
        return []


def notify_channel(*, title, message="", link=""):
    """채널 알림을 백그라운드로 발송."""
    _dispatch(lambda: send_slack_message(title=title, message=message, link=link))


def notify_dm_ax(ax_user_id, title="알림 제목", message="", link=""):
    """AX 사용자 1명에게 DM을 백그라운드로 발송."""
    _dispatch(lambda: send_slack_dm_ax(ax_user_id, title, message, link))


def notify_dm_ax_many(ax_user_ids, title="알림 제목", message="", link=""):
    """AX 사용자 여러 명에게 DM을 백그라운드로 순차 발송 (스레드 1개)."""
    ids = [uid for uid in ax_user_ids if uid is not None]
    if not ids:
        return

    def _job():
        for uid in ids:
            send_slack_dm_ax(uid, title, message, link)

    _dispatch(_job)
