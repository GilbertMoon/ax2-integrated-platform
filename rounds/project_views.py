from types import SimpleNamespace

from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, connection
from django.shortcuts import redirect, render

from accounts.permissions import is_operations_user
from rounds.forms import (
    EvaluationRoundForm,
    ProjectInfoForm,
)
from rounds.models import EvaluationRound


def _require_operations(user):
    if not is_operations_user(user):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied


def _project_rows():
    """
    프로젝트 회차의 기준 데이터는 project_info이다.

    project_info.id              = 프로젝트 회차 ID
    project_info.evaluationround_id = 연결된 평가 회차 ID
    """
    try:
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

            columns = [column[0] for column in cursor.description]

            return [
                dict(zip(columns, row, strict=True))
                for row in cursor.fetchall()
            ]

    except DatabaseError:
        return []


def _build_project(project_info):
    """
    project_info를 프로젝트 회차 화면용 객체로 변환한다.

    중요:
    - pk = project_info.id
    - evaluationround_id = 연결된 평가 회차 ID
    - EvaluationRound는 프로젝트의 본체가 아니라
      프로젝트에 연결된 평가 운영 정보이다.
    """

    evaluationround_id = project_info.get("evaluationround_id")

    evaluation_round = None

    if evaluationround_id:
        evaluation_round = (
            EvaluationRound.objects
            .filter(pk=evaluationround_id)
            .first()
        )

    # 프로젝트 이름/설명은 현재 연결된 평가 회차의
    # title / description을 사용한다.
    project_name = project_info.get("name") or f"프로젝트 회차 {project_info['id']}"

    project_description = project_info.get("description") or ""

    return SimpleNamespace(
        # =========================
        # 프로젝트 회차 식별정보
        # =========================
        pk=project_info["id"],
        project_id=project_info["id"],
        project_info_id=project_info["id"],

        # =========================
        # 프로젝트 기본정보
        # =========================
        name=project_name,
        title=project_name,
        description=project_description,

        # =========================
        # 프로젝트 기간
        # =========================
        project_start=project_info.get("team_start"),
        project_end=project_info.get("team_end"),

        # =========================
        # 연결된 평가 회차
        # =========================
        evaluationround_id=evaluationround_id,
        evaluation_round=evaluation_round,

        # =========================
        # 평가 운영정보
        # =========================
        status=(
            evaluation_round.status
            if evaluation_round
            else None
        ),

        status_display=(
            evaluation_round.get_status_display()
            if evaluation_round
            else "평가 회차 미연결"
        ),

        evaluation_start_at=(
            evaluation_round.evaluation_start_at
            if evaluation_round
            else None
        ),

        evaluation_end_at=(
            evaluation_round.evaluation_end_at
            if evaluation_round
            else None
        ),

        team_count=(
            evaluation_round.teams.count()
            if evaluation_round
            else 0
        ),

        participant_count=(
            evaluation_round.participants.count()
            if evaluation_round
            else 0
        ),
    )

@login_required
@login_required
def project_create(request):
    """프로젝트 회차와 평가 회차를 함께 생성한다."""

    _require_operations(request.user)

    if request.method == "POST":
        project_form = ProjectInfoForm(
            request.POST,
            prefix="project",
        )

        evaluation_form = EvaluationRoundForm(
            request.POST,
            prefix="evaluation",
        )

        if project_form.is_valid() and evaluation_form.is_valid():
            project_cleaned = project_form.cleaned_data
            evaluation_cleaned = evaluation_form.cleaned_data

            with transaction.atomic():
                # -----------------------------
                # 1. 평가 회차 생성
                # -----------------------------
                evaluation_round = EvaluationRound(
                    title=evaluation_cleaned["title"],
                    description=evaluation_cleaned["description"],
                    status=evaluation_cleaned["status"],
                    evaluation_start_at=(
                        evaluation_cleaned["evaluation_start_at"]
                    ),
                    evaluation_end_at=(
                        evaluation_cleaned["evaluation_end_at"]
                    ),
                    target_team_count=(
                        evaluation_cleaned["target_team_count"]
                    ),
                    team_score_weight=(
                        evaluation_cleaned["team_score_weight"]
                    ),
                    personal_score_weight=(
                        evaluation_cleaned["personal_score_weight"]
                    ),
                    tutor_score_weight=(
                        evaluation_cleaned["tutor_score_weight"]
                    ),
                    team_template=(
                        evaluation_cleaned["team_template"]
                    ),
                    peer_template=(
                        evaluation_cleaned["peer_template"]
                    ),
                    created_by=request.user,
                )

                evaluation_round.full_clean()
                evaluation_round.save()

                # -----------------------------
                # 2. 프로젝트 회차 생성
                # -----------------------------
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
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        [
                            project_cleaned["name"],
                            project_cleaned["description"],
                            project_cleaned["team_start"],
                            project_cleaned["team_end"],
                            evaluation_round.pk,
                        ],
                    )

                    project_id = cursor.fetchone()[0]

            return redirect(
                "rounds:project-detail",
                project_id=project_id,
            )

    else:
        project_form = ProjectInfoForm(
            prefix="project",
        )

        evaluation_form = EvaluationRoundForm(
            prefix="evaluation",
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
    """
    프로젝트 회차 상세.

    project_id는 반드시 project_info.id이다.
    """

    _require_operations(request.user)

    project_info = next(
        (
            row
            for row in _project_rows()
            if row["id"] == project_id
        ),
        None,
    )

    if project_info is None:
        from django.http import Http404

        raise Http404(
            f"프로젝트 회차 {project_id}를 찾을 수 없습니다."
        )

    project = _build_project(project_info)

    return render(
        request,
        "rounds/project_detail.html",
        {
            "project": project,
            "project_info": project_info,
            "evaluation_round": project.evaluation_round,
            "participant_count": project.participant_count,
            "team_count": project.team_count,
        },
    )

@login_required
def project_edit(request, project_id):
    """프로젝트 회차와 연결된 평가 회차 정보를 함께 수정한다."""

    _require_operations(request.user)

    project_info = next(
        (
            row
            for row in _project_rows()
            if row["id"] == project_id
        ),
        None,
    )

    if project_info is None:
        from django.http import Http404

        raise Http404(
            f"프로젝트 회차 {project_id}를 찾을 수 없습니다."
        )

    evaluation_round = (
        EvaluationRound.objects
        .filter(pk=project_info["evaluationround_id"])
        .first()
    )

    if evaluation_round is None:
        from django.http import Http404

        raise Http404(
            f"연결된 평가 회차 "
            f"{project_info['evaluationround_id']}를 찾을 수 없습니다."
        )

    if request.method == "POST":
        project_form = ProjectInfoForm(
            request.POST,
            prefix="project",
        )

        evaluation_form = EvaluationRoundForm(
            request.POST,
            instance=evaluation_round,
            prefix="evaluation",
        )

        if project_form.is_valid() and evaluation_form.is_valid():
            project_cleaned = project_form.cleaned_data
            evaluation_cleaned = evaluation_form.cleaned_data

            # ---------------------------------
            # 1. 평가 회차 저장
            # ---------------------------------
            evaluation_round.title = evaluation_cleaned["title"]
            evaluation_round.description = (
                evaluation_cleaned["description"]
            )
            evaluation_round.status = evaluation_cleaned["status"]
            evaluation_round.evaluation_start_at = (
                evaluation_cleaned["evaluation_start_at"]
            )
            evaluation_round.evaluation_end_at = (
                evaluation_cleaned["evaluation_end_at"]
            )
            evaluation_round.target_team_count = (
                evaluation_cleaned["target_team_count"]
            )
            evaluation_round.team_score_weight = (
                evaluation_cleaned["team_score_weight"]
            )
            evaluation_round.personal_score_weight = (
                evaluation_cleaned["personal_score_weight"]
            )
            evaluation_round.tutor_score_weight = (
                evaluation_cleaned["tutor_score_weight"]
            )
            evaluation_round.team_template = (
                evaluation_cleaned["team_template"]
            )
            evaluation_round.peer_template = (
                evaluation_cleaned["peer_template"]
            )

            evaluation_round.save()

            # ---------------------------------
            # 2. 프로젝트 회차 저장
            # ---------------------------------
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
                        project_cleaned["evaluationround_id"].pk,
                        project_id,
                    ],
                )

            return redirect(
                "rounds:project-detail",
                project_id=project_id,
            )

    else:
        project_form = ProjectInfoForm(
            initial={
                "name": project_info["name"],
                "description": project_info["description"],
                "team_start": project_info["team_start"],
                "team_end": project_info["team_end"],
                "evaluationround_id": evaluation_round,
            },
            prefix="project",
        )

        evaluation_form = EvaluationRoundForm(
            instance=evaluation_round,
            prefix="evaluation",
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
        },
    )