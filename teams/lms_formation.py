"""Team formation input scores; never updates published evaluation results."""

import random
from decimal import Decimal
from types import SimpleNamespace

from django.core import signing
from django.core.exceptions import ValidationError
from django.utils import timezone
from lms_modules.core.models import Assignment, Submission
from lms_modules.tutor.grading import _score_one
from lms_modules.tutor.models import GradingPolicy, RoundScore

from results.models import EvaluationResult
from results.services import calculate_final_score, calculate_seed
from rounds.models import EvaluationRound, RoundParticipant
from teams.application import (
    RoundNotEditableError,
    TeamVersionConflictError,
    create_auto_team_board,
)
from teams.django_backend import DjangoTeamsDataSource
from teams.models import TeamMembership

SALT = "teams.lms.formation.v1"


def selection(value):
    if not isinstance(value, dict) or type(value.get("enabled")) is not bool:
        raise ValidationError("LMS 포함 여부를 확인해 주세요.")
    enabled = value["enabled"]
    weight = value.get("weight", 0)
    if type(weight) is not int or not 0 <= weight <= 100:
        raise ValidationError("LMS 비율은 0~100 정수여야 합니다.")
    items = value.get("items", []) if enabled else []
    if not isinstance(items, list):
        raise ValidationError("과제 선택 형식이 올바르지 않습니다.")
    unique = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValidationError("과제 선택 형식이 올바르지 않습니다.")
        aid, rid = item.get("assignment_id"), item.get("round_id")
        if (
            type(aid) is not int
            or aid <= 0
            or (rid is not None and (type(rid) is not int or rid <= 0))
        ):
            raise ValidationError("과제 또는 회차 ID가 올바르지 않습니다.")
        if aid in unique and unique[aid] != rid:
            raise ValidationError("같은 과제를 서로 다른 회차로 중복 선택할 수 없습니다.")
        unique[aid] = rid
    if enabled and (not unique or weight == 0):
        raise ValidationError("LMS 포함 시 과제를 선택하고 비율을 1% 이상 지정해 주세요.")
    return {
        "enabled": enabled,
        "weight": weight if enabled else 0,
        "items": [{"assignment_id": a, "round_id": unique[a]} for a in sorted(unique)],
    }


def base_scores(participants, target_round):
    """Remove LMS contribution and renormalize, without rewriting stored results."""
    result, evidence = {}, {}
    for pid, uid in participants.items():
        history, used = [], []
        rows = (
            EvaluationResult.objects.filter(
                result_type="INDIVIDUAL",
                participant__user_id=uid,
                calculation_run__is_active=True,
                calculation_run__round__status="COMPLETED",
                final_score_raw__isnull=False,
            )
            .exclude(calculation_run__round_id=target_round)
            .select_related("calculation_run__round")
            .order_by("-calculation_run__round__completed_at", "-pk")
        )
        for row in rows:
            rnd = row.calculation_run.round
            w = Decimal(rnd.lms_score_weight) / 100
            if w == 1 or (w and row.lms_score_raw is None):
                continue
            if w:
                expected = calculate_final_score(
                    row.team_score_raw,
                    row.peer_score_raw,
                    row.tutor_score_raw,
                    row.lms_score_raw,
                    team_weight=Decimal(rnd.team_score_weight) / 100,
                    peer_weight=Decimal(rnd.personal_score_weight) / 100,
                    tutor_weight=Decimal(rnd.tutor_score_weight) / 100,
                    lms_weight=w,
                )
                if expected != row.final_score_raw:
                    raise ValidationError(
                        f"회차 {rnd.pk}의 현재 비율과 저장된 평가 결과가 일치하지 않습니다. 과거 계산 기준을 확인해 주세요."
                    )
            score = (row.final_score_raw - (row.lms_score_raw or Decimal(0)) * w) / (1 - w)
            if not 0 <= score <= 5:
                raise ValidationError(
                    "기존 평가 점수와 비율이 일치하지 않습니다. 과거 채점 설정을 확인해 주세요."
                )
            history.append(score)
            used.append(
                {
                    "result_id": row.pk,
                    "round_id": rnd.pk,
                    "final": str(row.final_score_raw),
                    "lms": str(row.lms_score_raw),
                    "lms_weight": rnd.lms_score_weight,
                    "base": str(score),
                }
            )
            if len(history) == 3:
                break
        result[pid] = calculate_seed(list(reversed(history)))
        evidence[str(pid)] = used
    return result, evidence


def calculate(round_id, raw):
    chosen = selection(raw)
    participants = dict(
        RoundParticipant.objects.filter(round_id=round_id).values_list("pk", "user_id")
    )
    base, history = base_scores(participants, round_id)
    evidence = {
        "selection": chosen,
        "calculated_at": timezone.now().isoformat(),
        "history": history,
        "students": {},
        "policy": {},
        "assignments": [],
    }
    if not chosen["enabled"]:
        return base, evidence
    ids = [x["assignment_id"] for x in chosen["items"]]
    assignments = list(Assignment.objects.filter(pk__in=ids).order_by("pk"))
    if {a.pk for a in assignments} != set(ids):
        raise ValidationError("삭제되었거나 존재하지 않는 과제가 있습니다. 다시 선택해 주세요.")
    now = timezone.now()
    if any(a.due_at >= now for a in assignments):
        raise ValidationError("마감 전 과제는 포함할 수 없습니다. 마감 후 선택해 주세요.")
    rid_by_a = {x["assignment_id"]: x["round_id"] for x in chosen["items"]}
    round_ids = {r for r in rid_by_a.values() if r is not None}
    if EvaluationRound.objects.filter(pk__in=round_ids).count() != len(round_ids):
        raise ValidationError("선택한 회차가 존재하지 않습니다.")
    allowed = {rid: round_assignment_ids(rid) for rid in round_ids}
    for aid, rid in rid_by_a.items():
        if rid is not None and aid not in allowed[rid]:
            raise ValidationError("선택 과제와 회차의 귀속 범위가 일치하지 않습니다.")
    policy = GradingPolicy.objects.order_by("pk").first() or GradingPolicy()
    evidence["policy"] = {
        f.name: getattr(policy, f.name)
        for f in policy._meta.fields
        if f.name not in ("id", "updated_at")
    }
    membership = {
        (m.participant.round_id, m.participant.user_id): m.team_id
        for m in TeamMembership.objects.filter(
            participant__round_id__in=round_ids, team__round_id__in=round_ids
        ).select_related("participant", "team")
        if m.participant.round_id == m.team.round_id
    }
    subs = list(Submission.objects.filter(assignment_id__in=ids))
    personal = {(s.student_id, s.assignment_id): s for s in subs if s.student_id is not None}
    team_subs = {(s.team_id, s.assignment_id): s for s in subs if s.team_id is not None}
    for a in assignments:
        if a.is_team and rid_by_a[a.pk] is None:
            raise ValidationError("팀 과제는 당시 팀 소속을 확인할 회차를 선택해야 합니다.")
        evidence["assignments"].append(
            {
                "id": a.pk,
                "title": a.title,
                "round_id": rid_by_a[a.pk],
                "due_at": a.due_at.isoformat(),
                "is_team": a.is_team,
                "is_required": a.is_required,
                "weight_tier": a.weight_tier,
                "late_penalty": a.late_penalty,
            }
        )
    combined = {}
    for pid, uid in participants.items():
        # Give each selected historical team task its own resolved team submission.
        applicable, mapped, details = [], {}, []
        for a in assignments:
            team_id = membership.get((rid_by_a[a.pk], uid)) if a.is_team else None
            if a.is_team and team_id is None:
                details.append({"assignment_id": a.pk, "status": "not_in_historical_team"})
                continue
            sub = team_subs.get((team_id, a.pk)) if a.is_team else personal.get((uid, a.pk))
            if sub is not None and sub.final_score is None:
                raise ValidationError(
                    f"미채점 제출물이 있습니다: 과제 {a.pk}, 학생 ID {uid}. 평가 후 다시 계산해 주세요."
                )
            applicable.append(a)
            if a.is_team and sub:
                mapped[(0, a.pk)] = sub
            details.append(
                {
                    "assignment_id": a.pk,
                    "team_id": team_id,
                    "submission_id": sub.pk if sub else None,
                    "score": sub.final_score if sub else None,
                    "submitted_at": sub.submitted_at.isoformat() if sub else None,
                }
            )
        score = _score_one(uid, SimpleNamespace(id=0), applicable, personal, mapped, policy, now)
        lms = Decimal(str(score.final)) / 20 if score.final is not None else None
        w = Decimal(chosen["weight"]) / 100
        mixed = (
            lms
            if w == 1
            else (
                base[pid] * (1 - w) + lms * w if base[pid] is not None and lms is not None else None
            )
        )
        combined[pid] = mixed
        evidence["students"][str(pid)] = {
            "student_id": uid,
            "base": str(base[pid]) if base[pid] is not None else None,
            "lms_total": score.final,
            "combined": str(mixed) if mixed is not None else None,
            "details": details,
        }
    return combined, evidence


def preview(round_id, request_data, raw, actor_id, *, scores_only=False):
    source = DjangoTeamsDataSource()
    current = source.get_round_for_auto_assignment(round_id)
    if current.status != "DRAFT":
        raise RoundNotEditableError("준비 중 회차에서만 팀을 편성할 수 있습니다.")
    if current.lock_version != request_data.lock_version:
        raise TeamVersionConflictError("팀 편성 내용이 변경되었습니다. 새로고침해 주세요.")
    scores, evidence = calculate(round_id, raw)
    excluded = set(request_data.excluded_participant_ids)
    assignable = (
        tuple(p for p in current.participant_ids if p not in excluded) or current.participant_ids
    )
    result = (
        None
        if scores_only
        else create_auto_team_board(
            round_id=round_id,
            lock_version=current.lock_version,
            participant_ids=assignable,
            seed_scores=scores,
            team_count=request_data.team_count,
            previous_teammate_pairs=source.get_previous_teammate_pairs(round_id, assignable),
            rng=random.Random(),
        )
    )
    evidence.update(
        round_id=round_id,
        lock_version=current.lock_version,
        actor_id=actor_id,
        seed_scores={str(p): str(s) if s is not None else None for p, s in scores.items()},
    )
    return result, signing.dumps(evidence, salt=SALT, compress=True), evidence


def decode(token, round_id, version, actor_id):
    try:
        value = signing.loads(token, salt=SALT, max_age=3600)
    except (signing.BadSignature, TypeError):
        raise ValidationError(
            "점수 계산이 만료되었거나 변경되었습니다. 점수 계산 또는 자동 배치를 다시 실행해 주세요."
        ) from None
    if (value["round_id"], value["lock_version"], value["actor_id"]) != (
        round_id,
        version,
        actor_id,
    ):
        raise ValidationError("점수 계산의 회차·사용자·버전이 일치하지 않습니다.")
    return value


def round_assignment_ids(round_id):
    rnd = EvaluationRound.objects.filter(pk=round_id).first()
    if rnd is None:
        raise ValidationError("선택한 회차가 없습니다.")
    ids = set()
    for values in RoundScore.objects.filter(round_id=round_id).values_list(
        "assignment_ids", flat=True
    ):
        ids.update(values)
    previous = (
        EvaluationRound.objects.filter(evaluation_end_at__lt=rnd.evaluation_end_at)
        .exclude(pk=round_id)
        .order_by("-evaluation_end_at")
        .first()
    )
    qs = Assignment.objects.filter(due_at__lte=rnd.evaluation_end_at)
    if previous:
        qs = qs.filter(due_at__gt=previous.evaluation_end_at)
    ids.update(qs.values_list("pk", flat=True))
    return ids
