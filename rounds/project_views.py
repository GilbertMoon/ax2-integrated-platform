from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import DatabaseError, connection, transaction
from django.http import Http404
from django.shortcuts import redirect, render

from accounts.permissions import is_operations_user
from rounds.forms import (
    ProjectEvaluationRoundForm,
    ProjectInfoForm,
)
from rounds.models import EvaluationRound, RoundParticipant
from rounds.services import participant_snapshot_values


def _require_operations(user):
    """운영 담당자만 프로젝트 회차를 관리할 수 있도록 제한한다."""
    if not is_operations_user(user):
        raise PermissionDenied


def _project_rows():
    """project_info 기준으로 프로젝트 회차 목록을 조회한다."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                pi.id,
                pi.name,
                pi.description,
                pi.evaluationround_id,
                pi.team_start,
                pi.team_end
            FROM project_info pi
            ORDER BY pi.id DESC
            """
        )

        columns = [
            column[0]
            for column in cursor.description
        ]

        return [
            dict(
                zip(
                    columns,
                    row,
                    strict=True,
                )
            )
            for row in cursor.fetchall()
        ]


def _get_project_info(project_id):
    """project_info에서 프로젝트 회차 하나를 조회한다."""
    project_info = next(
        (
            row
            for row in _project_rows()
            if row["id"] == project_id
        ),
        None,
    )

    if project_info is None:
        raise Http404(
            f"프로젝트 회차 {project_id}를 찾을 수 없습니다."
        )

    return project_info


def _get_evaluation_round(project_info):
    """프로젝트에 연결된 평가 회차를 조회한다."""
    evaluationround_id = project_info.get(
        "evaluationround_id"
    )

    if not evaluationround_id:
        return None

    return (
        EvaluationRound.objects
        .filter(pk=evaluationround_id)
        .first()
    )


def _build_project(project_info):
    """프로젝트 화면용 객체를 생성한다."""
    evaluation_round = _get_evaluation_round(
        project_info
    )

    project_name = (
        project_info.get("name")
        or f"프로젝트 회차 {project_info['id']}"
    )

    project_description = (
        project_info.get("description")
        or ""
    )

    team_count = 0

    if evaluation_round:
        team_count = evaluation_round.teams.count()

    participant_count = 0

    if evaluation_round:
        participant_count = (
            evaluation_round.participants.count()
        )

    return {
        "pk": project_info["id"],
        "project_id": project_info["id"],
        "project_info_id": project_info["id"],
        "name": project_name,
        "title": project_name,
        "description": project_description,
        "project_start": project_info.get(
            "team_start"
        ),
        "project_end": project_info.get(
            "team_end"
        ),
        "evaluationround_id": project_info.get(
            "evaluationround_id"
        ),
        "evaluation_round": evaluation_round,
        "status": (
            evaluation_round.status
            if evaluation_round
            else None
        ),
        "status_display": (
            evaluation_round.get_status_display()
            if evaluation_round
            else "평가 회차 미연결"
        ),
        "evaluation_start_at": (
            evaluation_round.evaluation_start_at
            if evaluation_round
            else None
        ),
        "evaluation_end_at": (
            evaluation_round.evaluation_end_at
            if evaluation_round
            else None
        ),
        "team_count": team_count,
        "participant_count": participant_count,
    }


def _save_round_participants(
    evaluation_round,
    users,
):
    """평가 회차 참가자와 snapshot 정보를 저장한다."""
    selected_users = list(users)

    selected_ids = {
        user.pk
        for user in selected_users
    }

    evaluation_round.participants.exclude(
        user_id__in=selected_ids
    ).delete()

    existing = {
        participant.user_id: participant
        for participant
        in evaluation_round.participants.all()
    }

    for user in selected_users:
        values = participant_snapshot_values(user)

        participant = existing.get(user.pk)

        if participant:
            for field, value in values.items():
                setattr(
                    participant,
                    field,
                    value,
                )

            participant.save(
                update_fields=tuple(
                    values.keys()
                )
            )
        else:
            RoundParticipant.objects.create(
                round=evaluation_round,
                user=user,
                **values,
            )


def _save_project_info(
    *,
    project_id,
    project_cleaned,
    evaluation_round_id,
):
    """project_info 테이블을 수정한다."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE project_info
            SET
                name = %s,
                description = %s,
                team_start = %s,
                team_end = %s,
                evaluationround_id = %s
            WHERE id = %s
            """,
            [
                project_cleaned["name"],
                project_cleaned["description"],
                project_cleaned["team_start"],
                project_cleaned["team_end"],
                evaluation_round_id,
                project_id,
            ],
        )


@login_required
def project_create(request):
    """프로젝트 회차와 연결된 평가 회차를 함께 생성한다."""
    _require_operations(request.user)

    if request.method == "POST":
        project_form = ProjectInfoForm(
            request.POST,
            prefix="project",
        )

        evaluation_form = ProjectEvaluationRoundForm(
            request.POST,
            prefix="evaluation",
        )

        if (
            project_form.is_valid()
            and evaluation_form.is_valid()
        ):
            project_cleaned = (
                project_form.cleaned_data
            )
            evaluation_cleaned = (
                evaluation_form.cleaned_data
            )

            try:
                with transaction.atomic():
                    # ---------------------------------
                    # 1. 평가 회차 생성
                    # ---------------------------------
                    evaluation_round = (
                        evaluation_form.save(
                            commit=False
                        )
                    )

                    # 신규 프로젝트에 연결되는 평가 회차는
                    # 항상 준비 중(DRAFT) 상태로 생성한다.
                    evaluation_round.status = (
                        EvaluationRound.Status.DRAFT
                    )

                    evaluation_round.created_by = (
                        request.user
                    )

                    evaluation_round.full_clean()
                    evaluation_round.save()

                    # ---------------------------------
                    # 2. 참가자 저장
                    # ---------------------------------
                    participants = (
                        evaluation_cleaned.get(
                            "participants"
                        )
                        or []
                    )

                    _save_round_participants(
                        evaluation_round,
                        participants,
                    )

                    # ---------------------------------
                    # 3. 프로젝트 생성
                    # ---------------------------------
                    with connection.cursor() as cursor:
                        cursor.execute(
                            """
                            INSERT INTO project_info (
                                name,
                                description,
                                team_start,
                                team_end,
                                evaluationround_id
                            )
                            VALUES (
                                %s,
                                %s,
                                %s,
                                %s,
                                %s
                            )
                            RETURNING id
                            """,
                            [
                                project_cleaned["name"],
                                project_cleaned[
                                    "description"
                                ],
                                project_cleaned[
                                    "team_start"
                                ],
                                project_cleaned[
                                    "team_end"
                                ],
                                evaluation_round.pk,
                            ],
                        )

                        project_id = (
                            cursor.fetchone()[0]
                        )

            except (
                DatabaseError,
                ValidationError,
            ) as error:
                evaluation_form.add_error(
                    None,
                    error,
                )
            else:
                return redirect(
                    "rounds:project-detail",
                    project_id=project_id,
                )

    else:
        project_form = ProjectInfoForm(
            prefix="project",
        )

        evaluation_form = (
            ProjectEvaluationRoundForm(
                prefix="evaluation",
            )
        )

    return render(
        request,
        "rounds/project_create.html",
        {
            "project_form": project_form,
            "evaluation_form": evaluation_form,
        },
    )


@login_required
def project_list(request):
    """프로젝트 회차 관리 목록."""
    _require_operations(request.user)

    project_infos = _project_rows()

    projects = [
        _build_project(project_info)
        for project_info in project_infos
    ]

    return render(
        request,
        "rounds/project_list.html",
        {
            "projects": projects,
        },
    )


@login_required
def project_detail(request, project_id):
    """프로젝트 회차 상세."""
    _require_operations(request.user)

    project_info = _get_project_info(
        project_id
    )

    project = _build_project(project_info)

    evaluation_round = project[
        "evaluation_round"
    ]

    return render(
        request,
        "rounds/project_detail.html",
        {
            "project": project,
            "project_info": project_info,
            "evaluation_round": evaluation_round,
            "participant_count": project[
                "participant_count"
            ],
            "team_count": project[
                "team_count"
            ],
        },
    )


@login_required
def project_edit(request, project_id):
    """프로젝트 회차와 연결된 평가 회차 설정을 수정한다."""
    _require_operations(request.user)

    project_info = _get_project_info(
        project_id
    )

    evaluation_round = _get_evaluation_round(
        project_info
    )

    if evaluation_round is None:
        raise Http404(
            "프로젝트에 연결된 평가 회차를 "
            "찾을 수 없습니다."
        )

    # 시작된 평가 회차는 기존 lifecycle 규칙에 따라
    # 프로젝트 설정 화면에서도 수정하지 않는다.
    if (
        evaluation_round.status
        != EvaluationRound.Status.DRAFT
    ):
        return render(
            request,
            "rounds/project_edit.html",
            {
                "project_form": None,
                "evaluation_form": None,
                "project_info": project_info,
                "project_id": project_id,
                "evaluation_round": evaluation_round,
                "read_only": True,
            },
        )

    if request.method == "POST":
        project_form = ProjectInfoForm(
            request.POST,
            prefix="project",
        )

        evaluation_form = (
            ProjectEvaluationRoundForm(
                request.POST,
                instance=evaluation_round,
                prefix="evaluation",
            )
        )

        if (
            project_form.is_valid()
            and evaluation_form.is_valid()
        ):
            project_cleaned = (
                project_form.cleaned_data
            )
            evaluation_cleaned = (
                evaluation_form.cleaned_data
            )

            try:
                with transaction.atomic():
                    # ---------------------------------
                    # 1. 평가 회차 설정 수정
                    # ---------------------------------
                    evaluation_round = (
                        evaluation_form.save(
                            commit=False
                        )
                    )

                    # status는 변경하지 않는다.
                    evaluation_round.status = (
                        EvaluationRound.Status.DRAFT
                    )

                    evaluation_round.full_clean()
                    evaluation_round.save()

                    # ---------------------------------
                    # 2. 참가자 저장
                    # ---------------------------------
                    participants = (
                        evaluation_cleaned.get(
                            "participants"
                        )
                        or []
                    )

                    _save_round_participants(
                        evaluation_round,
                        participants,
                    )

                    # ---------------------------------
                    # 3. 프로젝트 정보 수정
                    # ---------------------------------
                    _save_project_info(
                        project_id=project_id,
                        project_cleaned=project_cleaned,
                        evaluation_round_id=(
                            evaluation_round.pk
                        ),
                    )

            except (
                DatabaseError,
                ValidationError,
            ) as error:
                evaluation_form.add_error(
                    None,
                    error,
                )
            else:
                return redirect(
                    "rounds:project-detail",
                    project_id=project_id,
                )

    else:
        project_form = ProjectInfoForm(
            initial={
                "name": project_info["name"],
                "description": project_info[
                    "description"
                ],
                "team_start": project_info[
                    "team_start"
                ],
                "team_end": project_info[
                    "team_end"
                ],
            },
            prefix="project",
        )

        evaluation_form = (
            ProjectEvaluationRoundForm(
                instance=evaluation_round,
                prefix="evaluation",
            )
        )

        evaluation_form.fields[
            "participants"
        ].initial = (
            evaluation_round.participants.values_list(
                "user_id",
                flat=True,
            )
        )

    return render(
        request,
        "rounds/project_edit.html",
        {
            "project_form": project_form,
            "evaluation_form": evaluation_form,
            "project_info": project_info,
            "project_id": project_id,
            "evaluation_round": evaluation_round,
            "read_only": False,
        },
    )