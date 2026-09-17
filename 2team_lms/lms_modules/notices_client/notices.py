"""Core 공지(4조 `notices` 앱) 조회 wrapper.

Core `notices.Notice` 를 단일 원본(source of truth)으로 두고 읽기만 한다 —
LMS 쪽에 별도 공지 테이블/모델을 만들지 않는다. `notices` 앱은 `default` DB에
있고 LMS 코드와 같은 Django 프로세스에서 돌기 때문에 cross-DB 문제가 없다.

지연 import(함수 안에서 import): 앱 레지스트리 준비 전 순환참조를 피하기
위함 — `lms_modules.notifications.slack` 과 동일한 패턴.
"""

import logging

logger = logging.getLogger(__name__)


def active_notice_texts():
    """공개(is_published=True)된 Core 공지 제목을 최신순으로 반환.

    조회 실패 시 예외를 밖으로 던지지 않고 빈 리스트를 반환한다 —
    Core notices 앱 장애로 LMS 대시보드가 500 나면 안 된다.
    """
    try:
        from notices.services import active_notices

        return [notice.title for notice in active_notices()]
    except Exception:  # noqa: BLE001
        logger.exception("Core 공지 조회 실패")
        return []
