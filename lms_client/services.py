from __future__ import annotations

from typing import Optional

from .models import RoundScore


LMS_SCORE_MAX = 100.0
CORE_SCORE_MAX = 5.0


def get_round_score(round_id: int, student_id: int) -> Optional[RoundScore]:
    """2조 LMS의 회차별 학생 점수 스냅샷을 읽는다.

    LMS DB에는 쓰지 않으며, 반드시 별도 DB alias인 ``lms``를 사용한다.
    """
    return (
        RoundScore.objects.using("lms")
        .filter(round_id=round_id, student_id=student_id)
        .order_by("-closed_at")
        .first()
    )


def normalize_score(total: float | int | None) -> Optional[float]:
    """LMS 0~100 점수를 4조 0~5 점 척도로 변환한다."""
    if total is None:
        return None

    value = float(total)
    if not 0.0 <= value <= LMS_SCORE_MAX:
        raise ValueError(f"LMS score must be between 0 and 100: {value}")

    return round(value / 20.0, 2)


def get_normalized_score(round_id: int, student_id: int) -> Optional[float]:
    """회차·학생의 LMS 점수를 조회 후 4조 점수 척도로 변환한다."""
    snapshot = get_round_score(round_id, student_id)
    if snapshot is None:
        return None
    return normalize_score(snapshot.total)
