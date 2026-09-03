from types import SimpleNamespace

from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, connection
from django.shortcuts import render

from accounts.permissions import is_operations_user
from rounds.forms import ProjectInfoForm
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
                dict(zip(columns, row))
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
def project_create(request):
    """새 프로젝트 회차 생성."""

    _require_operations(request.user)

    if request.method == "POST":
        form = ProjectInfoForm(request.POST)

        if form.is_valid():
            # 다음 단계에서 project_info INSERT 연결
            pass
    else:
        form = ProjectInfoForm()

    return render(
        request,
        "rounds/project_create.html",
        {
            "form": form,
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