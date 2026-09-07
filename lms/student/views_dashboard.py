"""2조 LMS 학생 메인 대시보드."""

import calendar as _calendar
import datetime as dt
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts_client import services as accounts
from apps.github_sync import services as github_services
from apps.github_sync.models import StudentGithubAccount
from lms.identity import external_student_id
from lms.models import Assignment, Lesson, Submission, Todo

NOTICES = [
    "[안내] 과제 제출 마감은 각 과제의 마감일시 기준입니다.",
    "[안내] 팀 과제는 팀원 누구나 팀을 대신해 제출할 수 있습니다.",
    "[안내] 튜터 평가가 등록되면 해당 제출물은 재제출이 제한됩니다.",
]
UPCOMING_LIMIT = 5


def student_required(view_func):
    """로그인 + 학생 역할 확인."""

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not accounts.is_student(request.user.id):
            raise PermissionDenied("학생만 접근할 수 있습니다.")
        return view_func(request, *args, **kwargs)

    return _wrapped


@student_required
def dashboard(request):
    uid = request.user.id
    today = timezone.localdate()
    now = timezone.now()

    team = accounts.get_user_team(external_student_id(request))
    team_members = accounts.get_team_members(team.id) if team else []

    mine = Q(student_id=uid)
    if team:
        mine |= Q(team_id=team.id)
    my_subs = {s.assignment_id: s for s in Submission.objects.filter(mine)}

    def _applies(assignment):
        return not (assignment.is_team and not team)

    year, month = _resolve_month(request, today)
    selected = _resolve_selected_day(request, year, month, today)
    by_day = _calendar_events(year, month, my_subs, _applies)
    todo_days = set(
        Todo.objects.filter(
            student_id=uid, due_date__year=year, due_date__month=month
        ).values_list("due_date", flat=True)
    )
    weeks = _month_weeks(year, month, today, selected, by_day, todo_days)

    day_selected = bool(request.GET.get("d"))
    day_bucket = by_day.get(selected, {})
    day_lectures = day_bucket.get("lecture", [])
    day_assignments = day_bucket.get("assignment", [])

    todo_date = selected if day_selected else today
    todos = list(Todo.objects.filter(student_id=uid, due_date=todo_date))
    todo_done = sum(1 for todo in todos if todo.is_done)

    upcoming = []
    for assignment in Assignment.objects.order_by("due_at"):
        if not _applies(assignment) or assignment.id in my_subs:
            continue
        if now > assignment.due_at:
            continue
        due_local = timezone.localtime(assignment.due_at)
        upcoming.append(
            {
                "id": assignment.id,
                "title": assignment.title,
                "due": due_local,
                "dday": (due_local.date() - today).days,
                "allow_late": assignment.allow_late,
                "is_team": assignment.is_team,
            }
        )
    upcoming = upcoming[:UPCOMING_LIMIT]

    assignments = list(Assignment.objects.all())

    total = submitted = graded = 0
    for assignment in assignments:
        if not _applies(assignment):
            continue
        total += 1
        submission = my_subs.get(assignment.id)
        if submission:
            submitted += 1
            if submission.final_score is not None:
                graded += 1
    progress_pct = round(submitted / total * 100) if total else 0

    week_start = _resolve_week(request, today)
    week_end = week_start + dt.timedelta(days=6)
    week_assignments = [
        assignment
        for assignment in assignments
        if _applies(assignment)
        and week_start <= timezone.localtime(assignment.due_at).date() <= week_end
    ]
    week_submitted = sum(
        assignment.id in my_subs for assignment in week_assignments
    )
    week_ungraded = sum(
        assignment.id in my_subs
        and my_subs[assignment.id].final_score is None
        for assignment in week_assignments
    )
    week_total = len(week_assignments)
    week_pct = round(week_submitted / week_total * 100) if week_total else 0

    def _week_url(start):
        params = request.GET.copy()
        params["week"] = start.isoformat()
        return f"?{params.urlencode()}"

    prev_y, prev_m = (year - 1, 12) if month == 1 else (year, month - 1)
    next_y, next_m = (year + 1, 1) if month == 12 else (year, month + 1)

    github_enabled = github_services.enabled()
    github_account = (
        StudentGithubAccount.objects.filter(
            student_id=external_student_id(request)
        ).first()
        if github_enabled
        else None
    )

    return render(
        request,
        "lms/student/dashboard.html",
        {
            "notices": NOTICES,
            "cal": {
                "year": year,
                "month": month,
                "weeks": weeks,
                "prev": {"y": prev_y, "m": prev_m},
                "next": {"y": next_y, "m": next_m},
            },
            "selected": selected,
            "today": today,
            "day_selected": day_selected,
            "day_lectures": day_lectures,
            "day_assignments": day_assignments,
            "upcoming": upcoming,
            "assign_stats": {
                "total": total,
                "submitted": submitted,
                "graded": graded,
                "todo": total - submitted,
                "pct": progress_pct,
            },
            "submission_week": {
                "start": week_start,
                "end": week_end,
                "total": week_total,
                "submitted": week_submitted,
                "ungraded": week_ungraded,
                "pct": week_pct,
                "prev_url": _week_url(week_start - dt.timedelta(days=7)),
                "next_url": _week_url(week_start + dt.timedelta(days=7)),
            },
            "team": team,
            "team_members": team_members,
            "todos": todos,
            "todo_done": todo_done,
            "todo_date": todo_date,
            "todo_is_today": todo_date == today,
            "github_enabled": github_enabled,
            "github_account": github_account,
        },
    )


def _resolve_week(request, today):
    try:
        anchor = dt.date.fromisoformat(request.GET.get("week", today.isoformat()))
    except (TypeError, ValueError):
        anchor = today
    return anchor - dt.timedelta(days=anchor.weekday())


def _resolve_month(request, today):
    try:
        year = int(request.GET.get("y", today.year))
        month = int(request.GET.get("m", today.month))
        dt.date(year, month, 1)
        return year, month
    except (ValueError, TypeError):
        return today.year, today.month


def _resolve_selected_day(request, year, month, today):
    raw = request.GET.get("d")
    if raw:
        try:
            return dt.date.fromisoformat(raw)
        except ValueError:
            pass
    if (year, month) == (today.year, today.month):
        return today
    return dt.date(year, month, 1)


def _calendar_events(year, month, my_subs, applies):
    by_day = {}
    for assignment in Assignment.objects.filter(
        due_at__year=year, due_at__month=month
    ):
        if not applies(assignment):
            continue
        local = timezone.localtime(assignment.due_at)
        by_day.setdefault(local.date(), {}).setdefault("assignment", []).append(
            {
                "kind": "assignment",
                "title": assignment.title,
                "time": local.strftime("%H:%M"),
                "id": assignment.id,
                "done": assignment.id in my_subs,
                "is_team": assignment.is_team,
            }
        )
    for lesson in Lesson.objects.filter(
        lesson_date__year=year, lesson_date__month=month
    ):
        by_day.setdefault(lesson.lesson_date, {}).setdefault("lecture", []).append(
            {
                "kind": "lecture",
                "title": lesson.title,
                "time": "",
                "id": lesson.id,
            }
        )
    return by_day


def _month_weeks(year, month, today, selected, by_day, todo_days=frozenset()):
    cal = _calendar.Calendar(firstweekday=6)
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        row = []
        for day in week:
            bucket = by_day.get(day, {})
            assignments = bucket.get("assignment", [])
            row.append(
                {
                    "date": day,
                    "day": day.day,
                    "in_month": day.month == month,
                    "is_today": day == today,
                    "is_selected": day == selected,
                    "has_lecture": bool(bucket.get("lecture")),
                    "has_pending": any(not item["done"] for item in assignments),
                    "has_done": any(item["done"] for item in assignments),
                    "has_todo": day in todo_days,
                }
            )
        weeks.append(row)
    return weeks


def _redirect_to_day(raw_date):
    try:
        day = dt.date.fromisoformat(raw_date)
    except (TypeError, ValueError):
        return redirect("lms:dashboard")
    return redirect(
        f"{reverse('lms:dashboard')}?y={day.year}&m={day.month}&d={day.isoformat()}"
    )


@student_required
@require_POST
def todo_add(request):
    content = (request.POST.get("content") or "").strip()
    raw_date = request.POST.get("date")
    try:
        due = dt.date.fromisoformat(raw_date) if raw_date else timezone.localdate()
    except ValueError:
        due = timezone.localdate()
    if content:
        Todo.objects.create(
            student_id=request.user.id, content=content[:500], due_date=due
        )
    return _redirect_to_day(due.isoformat())


@student_required
@require_POST
def todo_toggle(request, pk):
    todo = Todo.objects.filter(pk=pk, student_id=request.user.id).first()
    if not todo:
        raise PermissionDenied("본인의 TODO만 변경할 수 있습니다.")
    todo.is_done = not todo.is_done
    todo.save(update_fields=["is_done"])
    return _redirect_to_day(todo.due_date.isoformat())


@student_required
@require_POST
def todo_delete(request, pk):
    todo = Todo.objects.filter(pk=pk, student_id=request.user.id).first()
    day = todo.due_date.isoformat() if todo else None
    if todo:
        todo.delete()
    return _redirect_to_day(day)
