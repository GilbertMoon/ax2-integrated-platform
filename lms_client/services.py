from __future__ import annotations

from typing import Iterable, Optional

from .models import RoundScore


LMS_DB_ALIAS = "assignment_lms"
LMS_SCORE_MAX = 100.0
CORE_SCORE_MAX = 5.0


def get_round_score(round_id: int, student_id: int) -> Optional[RoundScore]:
    """2조 LMS의 회차별 학생 점수 스냅샷을 읽는다.

    LMS DB에는 쓰지 않으며, 별도 DB alias인 ``assignment_lms``를 사용한다.
    """
    return (
        RoundScore.objects.using(LMS_DB_ALIAS)
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


def get_normalized_scores(round_id: int, student_ids: Iterable[int]) -> dict[int, float | None]:
    """한 회차의 여러 학생 LMS 점수를 한 번에 조회해 0~5 점 척도로 돌려준다.

    4조 채점 실행에서 학생마다 LMS DB를 개별 조회하지 않도록 배치 조회한다. 점수 마감
    스냅샷이 없는 학생은 결과 dict에 포함하지 않으며, 호출부는 이를 N/A로 처리한다.
    """
    ids = {int(student_id) for student_id in student_ids}
    if not ids:
        return {}

    snapshots = (
        RoundScore.objects.using(LMS_DB_ALIAS)
        .filter(round_id=round_id, student_id__in=ids)
        .order_by("student_id", "-closed_at")
    )
    scores: dict[int, float | None] = {}
    for snapshot in snapshots:
        scores.setdefault(snapshot.student_id, normalize_score(snapshot.total))
    return scores
