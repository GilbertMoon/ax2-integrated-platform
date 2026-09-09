import json
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from typing import Protocol

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from notifications.models import Notification
from notifications.services import notify_users
from results.models import CalculationRun, EvaluationResult
from rounds.models import RoundParticipant
from teams.application import (
    AutoTeamBoardResult,
    RoundNotEditableError,
    TeamVersionConflictError,
)
from teams.contracts import (
    AutoAssignmentRequest,
    TeamContractError,
    TeamSaveRequest,
    auto_team_board_response,
    management_team_response,
    saved_team_board_response,
    student_team_response,
)
from teams.domain import TeamBoard
from teams.queries import (
    ManagementTeamView,
    RoundParticipantNotFoundError,
    StudentRoundOption,
    StudentTeamView,
)
from teams.services import (
    AssignmentValidationError,
    ImbalanceConfirmationRequired,
    UnassignedParticipantsConfirmationRequired,
)


class TeamsHttpBackend(Protocol):
    """실제 Django ORM 어댑터가 제공해야 하는 HTTP 연결 인터페이스다."""

    def get_student_team(self, user_id: int, round_id: int | None = None) -> StudentTeamView: ...

    def get_student_round_options(self, user_id: int) -> tuple[StudentRoundOption, ...]: ...

    def get_management_team(self, round_id: int) -> ManagementTeamView: ...

    def create_auto_assignment(
        self,
        round_id: int,
        request_data: AutoAssignmentRequest,
    ) -> AutoTeamBoardResult: ...

    def save_team_configuration(
        self,
        round_id: int,
        actor_id: int,
        request_data: TeamSaveRequest,
    ) -> TeamBoard: ...


class TeamsBackendNotConfiguredError(RuntimeError):
    """실제 ORM 연결이 아직 구성되지 않았음을 나타낸다."""


def get_teams_backend() -> TeamsHttpBackend:
    from teams.django_backend import build_django_teams_backend

    return build_django_teams_backend()


@require_GET
def team_ui_preview(request: HttpRequest) -> HttpResponse:
    """ORM 병합 전 로컬 UI 검토에만 사용하는 화면이다."""
    names = (
        "김민수",
        "이영희",
        "박지훈",
        "최서연",
        "정현우",
        "한지민",
        "윤서준",
        "임수아",
        "강도윤",
        "송하윤",
        "조현준",
        "배지우",
        "문시우",
        "오서윤",
        "신지호",
        "권나연",
        "안유진",
        "홍준서",
        "김서현",
        "이도윤",
        "박서아",
        "최준혁",
        "정다은",
        "한예준",
        "윤하린",
        "임도현",
        "강서진",
        "송민재",
        "조유나",
        "배현우",
        "문지아",
        "오준영",
        "신예린",
        "권도하",
        "안수빈",
    )
    teams = []
    for team_index in range(7):
        members = [
            {
                "participant_id": index + 101,
                "student_number": f"A{index + 1:03d}",
                "display_name": name,
            }
            for index, name in enumerate(names)
            if index % 7 == team_index
        ]
        teams.append(
            {"team_number": team_index + 1, "name": f"{team_index + 1}팀", "members": members}
        )
    role = request.GET.get("role", "tutor")
    state = request.GET.get("state", "configured")
    configured = state != "empty"
    unassigned_members = []
    if role == "tutor" and state == "unassigned":
        unassigned_members = teams[-1]["members"][-3:]
        teams[-1]["members"] = teams[-1]["members"][:-3]
    return render(
        request,
        "teams/workspace.html",
        {
            "role": role,
            "my_participant_id": 101 if role == "student" else None,
            "team_data": {
                "round_id": 10,
                "round_status": "DRAFT" if configured else "COMPLETED",
                "lock_version": 1,
                "is_configured": configured,
                "is_read_only": False,
                "teams": teams if configured else [],
                "unassigned_members": unassigned_members,
                "my_participant_id": 101,
            },
            "preview_mode": True,
        },
    )


@require_GET
def student_team_page(request: HttpRequest) -> HttpResponse:
    permission_error = _permission_error(request, allowed_roles={"student"})
    if permission_error is not None:
        return permission_error
    backend = get_teams_backend()
    round_param = request.GET.get("round")
    round_id = int(round_param) if round_param and round_param.isdigit() else None
    round_options = backend.get_student_round_options(request.user.id)
    try:
        view = backend.get_student_team(request.user.id, round_id)
    except LookupError:
        return render(
            request,
            "teams/workspace.html",
            {
                "role": "student",
                "team_data": {
                    "round_id": None,
                    "round_status": "NONE",
                    "lock_version": 0,
                    "is_configured": False,
                    "is_read_only": True,
                    "teams": [],
                    "unassigned_members": [],
                    "my_participant_id": None,
                },
                "my_participant_id": None,
                "round_options": round_options,
                "selected_round_id": round_id,
            },
        )
    return render(
        request,
        "teams/workspace.html",
        {
            "role": "student",
            "team_data": student_team_response(view),
            "my_participant_id": view.participant_id,
            "round_options": round_options,
            "selected_round_id": view.round_id,
            "result_summary": _student_team_result_summary(
                view.round_id, view.team.team_number if view.team else None
            ),
        },
    )


def _student_team_result_summary(round_id: int, team_number: int | None) -> dict | None:
    """학생 '내 팀' 화면 상단에 보여줄 팀 결과 요약 - 튜터가 공개한 항목만 채운다.

    팀 1위/내 팀 순위 둘 다 비공개면 요약 자체를 그리지 않는다(화면에 빈 카드만
    남는 걸 피하려고 None을 돌려준다).
    """
    run = CalculationRun.objects.filter(round_id=round_id, is_active=True).first()
    if not run:
        return None

    winner = None
    if run.winner_published_at:
        winner_result = (
            run.results.filter(result_type=EvaluationResult.ResultType.TEAM, primary_rank=1)
            .select_related("team")
            .first()
        )
        if winner_result:
            winner = {"name": winner_result.team.name, "score": winner_result.team_score_raw}

    my_team = None
    if run.team_ranking_published_at and team_number is not None:
        my_result = (
            run.results.filter(
                result_type=EvaluationResult.ResultType.TEAM,
                team__round_id=round_id,
                team__team_number=team_number,
            )
            .select_related("team")
            .first()
        )
        if my_result and my_result.primary_rank:
            my_team = {
                "team_name": my_result.team.name,
                "rank": my_result.primary_rank,
                "score": my_result.team_score_raw,
            }

    if winner is None and my_team is None:
        return None
    return {"winner": winner, "my_team": my_team}


@require_GET
def management_team_page(request: HttpRequest, round_id: int) -> HttpResponse:
    permission_error = _permission_error(request, allowed_roles={"tutor"})
    if permission_error is not None:
        return permission_error
    try:
        view = get_teams_backend().get_management_team(round_id)
    except LookupError:
        return _error_response("not_found", "회차가 없습니다.", 404)
    from teams.models import TeamFormationSnapshot
    team_data = management_team_response(view)
    snapshot = TeamFormationSnapshot.objects.filter(round_id=round_id, version=team_data['lock_version']).first()
    if snapshot is not None:
        team_data['formation_evidence'] = snapshot.evidence
        team_data['seed_scores'] = snapshot.evidence['seed_scores']
    return render(
        request,
        "teams/workspace.html",
        {
            "role": "tutor",
            "team_data": team_data,
            "my_participant_id": None,
            "auto_url": f"/teams/manage/rounds/{round_id}/teams/auto/",
            "save_url": f"/teams/manage/rounds/{round_id}/teams/save/",
            # 저장 뒤 무엇을 해야 하는지 화면에서 바로 알려주기 위한 다음 단계 주소다.
            "next_url": reverse("rounds:reviews", kwargs={"round_id": round_id}),
            "preview_mode": False,
        },
    )


@require_GET
def student_team_view(request: HttpRequest) -> JsonResponse:
    permission_error = _permission_error(request, allowed_roles={"student"})
    if permission_error is not None:
        return permission_error
    try:
        view = get_teams_backend().get_student_team(request.user.id)
        return JsonResponse(student_team_response(view))
    except RoundParticipantNotFoundError as error:
        return _error_response("not_found", str(error), 404)
    except LookupError as error:
        return _error_response("not_found", str(error), 404)


@require_GET
def management_team_view(request: HttpRequest, round_id: int) -> JsonResponse:
    permission_error = _permission_error(request, allowed_roles={"tutor"})
    if permission_error is not None:
        return permission_error
    try:
        view = get_teams_backend().get_management_team(round_id)
        return JsonResponse(management_team_response(view))
    except LookupError as error:
        return _error_response("not_found", str(error), 404)


@require_POST
def auto_assignment_view(request: HttpRequest, round_id: int) -> JsonResponse:
    permission_error = _permission_error(request, allowed_roles={"tutor"})
    if permission_error is not None:
        return permission_error
    try:
        payload = _json_payload(request)
        request_data = AutoAssignmentRequest.from_payload(payload)
        if 'lms_selection' in payload:
            from teams.lms_formation import preview
            result, token, evidence = preview(round_id, request_data, payload['lms_selection'], request.user.id, scores_only=payload.get('scores_only') is True)
            body = auto_team_board_response(result) if result is not None else {}
            body.update(formation_token=token, formation_evidence=evidence)
            return JsonResponse(body)
        result = get_teams_backend().create_auto_assignment(round_id, request_data)
        return JsonResponse(auto_team_board_response(result))
    except ValidationError as error:
        return _error_response('invalid_request', ' '.join(error.messages), 400)
    except (TeamContractError, AssignmentValidationError) as error:
        return _error_response("invalid_request", str(error), 400)
    except TeamVersionConflictError as error:
        return _error_response("version_conflict", str(error), 409)
    except RoundNotEditableError as error:
        return _error_response("round_not_editable", str(error), 409)
    except LookupError as error:
        return _error_response("not_found", str(error), 404)


@require_POST
def save_team_view(request: HttpRequest, round_id: int) -> JsonResponse:
    permission_error = _permission_error(request, allowed_roles={"tutor"})
    if permission_error is not None:
        return permission_error
    try:
        payload = _json_payload(request)
        request_data = TeamSaveRequest.from_payload(round_id, payload)
        evidence = None
        if payload.get('formation_token'):
            from teams.lms_formation import decode
            evidence = decode(payload['formation_token'], round_id, request_data.board.lock_version, request.user.id)
        if payload.get('formation_required') and evidence is None:
            raise ValidationError('점수 계산 또는 자동 배치를 실행해 계산 근거를 먼저 확인해 주세요.')
        with transaction.atomic():
            board = get_teams_backend().save_team_configuration(round_id, request.user.id, request_data)
            if evidence is not None:
                from teams.models import TeamFormationSnapshot
                evidence['saved_teams'] = [{'team_number': t.team_number, 'participant_ids': list(t.participant_ids)} for t in board.teams]
                TeamFormationSnapshot.objects.create(round_id=round_id, actor_id=request.user.id, version=board.lock_version, evidence=evidence)
        _notify_team_assignments(board)
        return JsonResponse(saved_team_board_response(board))
    except ValidationError as error:
        return _error_response('invalid_request', ' '.join(error.messages), 400)
    except ImbalanceConfirmationRequired as error:
        return _error_response("imbalance_confirmation_required", str(error), 409)
    except UnassignedParticipantsConfirmationRequired as error:
        return _error_response("unassigned_confirmation_required", str(error), 409)
    except TeamVersionConflictError as error:
        return _error_response("version_conflict", str(error), 409)
    except RoundNotEditableError as error:
        return _error_response("round_not_editable", str(error), 409)
    except (TeamContractError, AssignmentValidationError) as error:
        return _error_response("invalid_request", str(error), 400)
    except LookupError as error:
        return _error_response("not_found", str(error), 404)


def _notify_team_assignments(board: TeamBoard) -> None:
    """팀 편성이 저장될 때마다 그 팀 소속 학생에게 배정 알림을 보낸다."""
    for team in board.teams:
        members = RoundParticipant.objects.filter(pk__in=team.participant_ids).select_related(
            "user"
        )
        notify_users(
            (member.user for member in members),
            category=Notification.Category.TEAM_CREATED,
            title="팀이 배정되었습니다",
            message=f"'{team.name}'에 배정되었습니다.",
            # "teams:student-team"은 JS가 fetch로 부르는 JSON API라 브라우저로 직접 열면
            # 안 된다 - 사이드바 "내 팀"이 실제로 쓰는 HTML 페이지 경로를 써야 한다.
            link=reverse("student-team-page"),
        )


def _json_payload(request: HttpRequest) -> dict[str, object]:
    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise TeamContractError("request body must be valid JSON") from error
    if not isinstance(payload, dict):
        raise TeamContractError("request body must be a JSON object")
    return payload


def _permission_error(
    request: HttpRequest,
    *,
    allowed_roles: set[str],
) -> JsonResponse | None:
    user = request.user
    if not getattr(user, "is_authenticated", False):
        return _error_response("authentication_required", "login is required", 401)
    # 권한 정의는 accounts가 소유하고 teams는 전달받은 역할과 staff 여부만 사용한다.
    role = getattr(user, "role", None)
    normalized_role = role.lower() if isinstance(role, str) else None
    if not getattr(user, "is_staff", False) and normalized_role not in allowed_roles:
        return _error_response("permission_denied", "permission denied", 403)
    return None


def _error_response(code: str, message: str, status: int) -> JsonResponse:
    return JsonResponse({"error": {"code": code, "message": message}}, status=status)


def _service_unavailable_response() -> JsonResponse:
    return _error_response(
        "teams_backend_not_configured",
        "팀 편성 데이터 연결이 아직 준비되지 않았습니다.",
        503,
    )


@require_POST
def send_team_announcement_view(request: HttpRequest, team_id: int) -> HttpResponse:
    """선택한 조(팀)의 모든 팀원들에게 일괄 공지 이메일을 발송합니다."""
    from django.contrib import messages
    from django.shortcuts import get_object_or_404, redirect

    from accounts.email_services import send_tutor_announcement_email
    from teams.models import Team

    permission_error = _permission_error(request, allowed_roles={"tutor"})
    if permission_error is not None:
        return permission_error

    team = get_object_or_404(Team, pk=team_id)
    subject = request.POST.get("subject", f"[{team.name}] 팀 공지사항").strip()
    message = request.POST.get("message", f"안녕하세요, {team.name} 팀원 공지사항입니다.").strip()

    recipient_emails = list(team.memberships.values_list("participant__user__email", flat=True))
    sent_count = send_tutor_announcement_email(subject, message, recipient_emails)

    messages.success(request, f"'{team.name}' 팀원에게 공지 메일 {sent_count}건을 발송했습니다.")
    return redirect(request.META.get("HTTP_REFERER", "/manage/"))


@require_GET
def lms_formation_catalog(request, round_id):
    permission_error = _permission_error(request, allowed_roles={'tutor'})
    if permission_error is not None:
        return permission_error
    from django.core.paginator import Paginator
    from rounds.models import EvaluationRound
    from lms_modules.core.models import Assignment
    from teams.models import TeamFormationSnapshot
    if not EvaluationRound.objects.filter(pk=round_id).exists():
        return _error_response('not_found', '회차가 없습니다.', 404)
    qs = Assignment.objects.filter(due_at__lt=timezone.now()).order_by('-due_at', '-pk')
    source_id = request.GET.get('source_round', '')
    if source_id:
        if not source_id.isdigit():
            return _error_response('invalid_request', '회차를 확인해 주세요.', 400)
        from teams.lms_formation import round_assignment_ids
        try:
            ids = round_assignment_ids(int(source_id))
        except ValidationError as error:
            return _error_response('invalid_request', '; '.join(error.messages), 400)
        qs = qs.filter(pk__in=ids)
    if request.GET.get('q'):
        qs = qs.filter(title__icontains=request.GET['q'])
    if request.GET.get('all_ids') == '1':
        return JsonResponse({'ids':list(qs.values_list('pk', flat=True))})
    page = Paginator(qs, 30).get_page(request.GET.get('page'))
    latest = TeamFormationSnapshot.objects.filter(round_id=round_id).first()
    return JsonResponse({'items':list(page.object_list.values('id','title','is_team','due_at')),
        'page':page.number,'pages':page.paginator.num_pages,'total':page.paginator.count,
        'rounds':list(EvaluationRound.objects.order_by('-created_at').values('id','title')),
        'saved':latest.evidence if latest else None})
