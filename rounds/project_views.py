from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import DatabaseError, connection
from django.shortcuts import get_object_or_404, render

from accounts.permissions import is_operations_user
from rounds.models import EvaluationRound
from rounds.services import rounds_dashboard_rows


def _require_operations(user):
    if not is_operations_user(user):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied


def _project_info_map():
    """Read the shared project_info table without making it a Django-owned table.

    The project period is currently maintained in the shared DB schema.  The
    management UI therefore reads only the agreed columns and does not attempt
    to migrate or redefine that table here.
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, evaluationround_id, team_start, team_end
                FROM project_info
                """
            )
            return {
                row[1]: {
                    "id": row[0],
                    "team_start": row[2],
                    "team_end": row[3],
                }
                for row in cursor.fetchall()
            }
    except DatabaseError:
        # A local development DB may not have the shared project_info table yet.
        # The project page still remains usable; project dates are simply blank.
        return {}


@login_required
def project_list(request):
    """Project-round management landing page.

    EvaluationRound remains the current operational round identifier, while
    project_info supplies the project/team period.  This keeps the page useful
    during the ongoing DB integration without conflating the evaluation setup
    screen with project administration.
    """
    _require_operations(request.user)
    project_infos = _project_info_map()
    projects = list(rounds_dashboard_rows())
    for project in projects:
        info = project_infos.get(project.pk, {})
        project.project_info_id = info.get("id")
        project.project_start = info.get("team_start")
        project.project_end = info.get("team_end")
    return render(request, "rounds/project_list.html", {"projects": projects})


@login_required
def project_detail(request, round_id):
    _require_operations(request.user)
    project = get_object_or_404(EvaluationRound, pk=round_id)
    project_info = _project_info_map().get(project.pk, {})

    context = {
        "project": project,
        "project_info": project_info,
        "participant_count": project.participants.count(),
        "team_count": project.teams.count(),
    }
    return render(request, "rounds/project_detail.html", context)
