# apps/student/views_dashboard.py
# 🧑‍🎓 학생 메인 대시보드 (PRD 7장 "학생 대시보드").
# 학생 A(과제 목록/제출)·학생 B(재제출/결과)와 별개 — 이 파일은 홈 대시보드 전용.
#
# 목업: docs/mockups/student-dashboard.html — 바꾼 부분:
#   - 평가 진행률 카드 → 별도 박스 없이 "다가오는 마감" 패널에 진행률·개수 통합
#   - 최근 공개 결과 → 100점 만점 기준 (5점 척도·가중합산은 ERD §4.3 폐기안)
#   - 공지 배너 → Core notices 앱을 원본으로 조회 (lms_modules.notices_client)
#   - 캘린더 = Assignment.due_at + Lesson.lesson_date, 셀에 제목+색상 태그로 표시
#     (미제출 과제를 맨 위로, 그다음 제출완료/강의/할일 순 · 최대 2개 + "+N개")
#   - 캘린더 아래 패널 = 평소엔 "다가오는 마감"(미제출·마감 전 과제 D-day순 + 진행률),
#     날짜를 누르면(?d=) 그날 일정으로 전환, 패널의 "← 다가오는 마감"으로 복귀
#
# 외부 계정/팀 데이터는 apps/accounts_client/services.py 헬퍼로만 접근.
# 사용자 role / 네비게이션은 apps/common/context_processors.py 가 처리 → nav_role 안 넘김.

import calendar as _calendar
import datetime as dt
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from lms_modules.accounts_client import services as accounts
from lms_modules.core.models import Assignment, Lesson, Submission, Todo
from lms_modules.github_sync import services as github_services
from lms_modules.github_sync.models import StudentGithubAccount
from lms_modules.notices_client.notices import active_notices_data

from .identity import external_student_id

UPCOMING_LIMIT = 5
RECENT_LECTURES_LIMIT = 3


@login_required
def home(request):
    """Send users from the site root to the dashboard for their role."""
    if accounts.is_tutor(request.user.id):
        return redirect("lms:tutor:dashboard")
    if accounts.is_student(request.user.id):
        return redirect("lms:student:dashboard")
    raise PermissionDenied("접근 가능한 역할이 없습니다.")


def student_required(view_func):
    """로그인 + role=STUDENT (accounts.is_student)."""

    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not accounts.is_student(request.user.id):
            raise PermissionDenied("학생만 접근할 수 있습니다.")
        return view_func(request, *args, **kwargs)

    return _wrapped


# =========================================================
# 대시보드
# =========================================================

@student_required
def dashboard(request):
    uid = request.user.id
    today = timezone.localdate()
    now = timezone.now()

    # 내 팀 (없으면 None)
    team = accounts.get_user_team(external_student_id(request))
    team_members = accounts.get_team_members(team.id) if team else []

    # 내 제출물 = 내 개인 제출 + (팀이 있으면) 내 팀 제출
    mine = Q(student_id=uid)
    if team:
        mine |= Q(team_id=team.id)
    my_subs = {s.assignment_id: s for s in Submission.objects.filter(mine)}

    # 학생에게 유효한 과제만 (개인 과제 전체 + 팀 과제는 팀이 있을 때)
    def _applies(a):
        return not (a.is_team and not team)

    # ── 캘린더 ──
    year, month = _resolve_month(request, today)
    selected = _resolve_selected_day(request, year, month, today)
    by_day = _calendar_events(year, month, my_subs, _applies)
    todo_map = {}
    for t in Todo.objects.filter(
        student_id=uid, due_date__year=year, due_date__month=month
    ):
        todo_map.setdefault(t.due_date, []).append(t.content)
    weeks = _month_weeks(year, month, today, selected, by_day, todo_map)

    day_selected = bool(request.GET.get("d"))
    day_bucket = by_day.get(selected, {})
    day_lectures = day_bucket.get("lecture", [])
    day_assignments = day_bucket.get("assignment", [])

    # ── TODO — 보고 있는 날짜(날짜 선택 시 그 날, 아니면 오늘) 기준 ──
    todo_date = selected if day_selected else today
    todos = list(Todo.objects.filter(student_id=uid, due_date=todo_date))
    todo_done = sum(1 for t in todos if t.is_done)

    # ── 다가오는 마감 (미제출 + 아직 마감 전 과제, 마감 임박순) ──
    # "다가오는" 마감이므로 이미 마감이 지난 과제는 제외한다.
    upcoming = []
    for a in Assignment.objects.order_by("due_at"):
        if not _applies(a) or a.id in my_subs:
            continue
        if now > a.due_at:
            continue
        due_local = timezone.localtime(a.due_at)
        upcoming.append({
            "id": a.id,
            "title": a.title,
            "due": due_local,
            "dday": (due_local.date() - today).days,
            "allow_late": a.allow_late,
            "is_team": a.is_team,
        })
    upcoming = upcoming[:UPCOMING_LIMIT]

    # ── 최근 강의 목록 (최근 등록된 순) ──
    recent_lectures = list(
        Lesson.objects.order_by("-created_at")[:RECENT_LECTURES_LIMIT]
    )

    assignments = list(Assignment.objects.all())

    # ── 내 과제 현황 ──
    total = submitted = graded = 0
    for a in assignments:
        if not _applies(a):
            continue
        total += 1
        s = my_subs.get(a.id)
        if s:
            submitted += 1
            if s.final_score is not None:
                graded += 1
    progress_pct = round(submitted / total * 100) if total else 0

    # ── 주간 과제 제출 현황 ──
    week_start = _resolve_week(request, today)
    week_end = week_start + dt.timedelta(days=6)
    week_assignments = [
        a for a in assignments
        if _applies(a) and week_start <= timezone.localtime(a.due_at).date() <= week_end
    ]
    week_submitted = sum(a.id in my_subs for a in week_assignments)
    week_ungraded = sum(
        a.id in my_subs and my_subs[a.id].final_score is None
        for a in week_assignments
    )
    week_total = len(week_assignments)
    week_pct = round(week_submitted / week_total * 100) if week_total else 0

    def _week_url(start):
        params = request.GET.copy()
        params["week"] = start.isoformat()
        return f"?{params.urlencode()}"

    prev_y, prev_m = (year - 1, 12) if month == 1 else (year, month - 1)
    next_y, next_m = (year + 1, 1) if month == 12 else (year, month + 1)

    # GitHub 연동 (lms_modules.github_sync) — 키 미설정 시 카드 자체를 숨긴다
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
        "lms_ui/student/dashboard.html",
        {
            "notices_detail": active_notices_data(),
            "cal": {
                "year": year, "month": month, "weeks": weeks,
                "prev": {"y": prev_y, "m": prev_m},
                "next": {"y": next_y, "m": next_m},
            },
            "selected": selected,
            "today": today,
            "day_selected": day_selected,
            "day_lectures": day_lectures,
            "day_assignments": day_assignments,
            "upcoming": upcoming,
            "recent_lectures": recent_lectures,
            "assign_stats": {
                "total": total, "submitted": submitted, "graded": graded,
                "todo": total - submitted, "pct": progress_pct,
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
            "team": team, "team_members": team_members,
            "todos": todos,
            "todo_done": todo_done,
            "todo_date": todo_date,
            "todo_is_today": todo_date == today,
            "github_enabled": github_enabled,
            "github_account": github_account,
        },
    )


def _resolve_week(request, today):
    """week 쿼리의 날짜가 속한 주(월요일 시작)를 반환한다."""
    try:
        anchor = dt.date.fromisoformat(request.GET.get("week", today.isoformat()))
    except (TypeError, ValueError):
        anchor = today
    return anchor - dt.timedelta(days=anchor.weekday())


def _resolve_month(request, today):
    try:
        year = int(request.GET.get("y", today.year))
        month = int(request.GET.get("m", today.month))
        dt.date(year, month, 1)  # 유효성
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
    """해당 월의 {date: {"assignment": [...], "lecture": [...]}}.
    과제 항목엔 done(내가 제출했는지) 플래그가 붙는다."""
    by_day = {}
    for a in Assignment.objects.filter(due_at__year=year, due_at__month=month):
        if not applies(a):
            continue
        local = timezone.localtime(a.due_at)
        by_day.setdefault(local.date(), {}).setdefault("assignment", []).append({
            "kind": "assignment",
            "title": a.title,
            "time": local.strftime("%H:%M"),
            "id": a.id,
            "done": a.id in my_subs,
            "is_team": a.is_team,
        })
    for lesson in Lesson.objects.filter(lesson_date__year=year, lesson_date__month=month):
        by_day.setdefault(lesson.lesson_date, {}).setdefault("lecture", []).append(
            {"kind": "lecture", "title": lesson.title, "time": "", "id": lesson.id}
        )
    return by_day


def _month_weeks(year, month, today, selected, by_day, todo_map=None):
    """cal.weeks 셀 목록. items = 그날 표시할 항목(제목+색상) 최대 2개
    — 미제출 과제를 맨 위로, 그다음 제출완료/강의/할일 순."""
    todo_map = todo_map or {}
    cal = _calendar.Calendar(firstweekday=6)  # 일요일 시작
    weeks = []
    for week in cal.monthdatescalendar(year, month):
        row = []
        for d in week:
            bucket = by_day.get(d, {})
            assigns = bucket.get("assignment", [])
            lectures = bucket.get("lecture", [])
            day_todos = todo_map.get(d, [])

            items = (
                [{"cat": "r", "title": a["title"]} for a in assigns if not a["done"]]
                + [{"cat": "g", "title": a["title"]} for a in assigns if a["done"]]
                + [{"cat": "b", "title": lec["title"]} for lec in lectures]
                + [{"cat": "p", "title": content} for content in day_todos]
            )

            row.append({
                "date": d,
                "day": d.day,
                "in_month": d.month == month,
                "is_today": d == today,
                "is_selected": d == selected,
                "has_lecture": bool(lectures),
                "has_pending": any(not x["done"] for x in assigns),
                "has_done": any(x["done"] for x in assigns),
                "has_todo": d in todo_map,
                "items": items[:2],
                "more_count": max(0, len(items) - 2),
            })
        weeks.append(row)
    return weeks


# =========================================================
# TODO (학생 본인 항목 CRUD — Todo 모델)
# =========================================================

def _redirect_to_day(raw_date):
    """편집한 날짜를 유지한 채 대시보드로 돌아간다."""
    try:
        d = dt.date.fromisoformat(raw_date)
    except (TypeError, ValueError):
        return redirect("lms:student:dashboard")
    return redirect(
        f"{reverse('lms:student:dashboard')}?y={d.year}&m={d.month}&d={d.isoformat()}"
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
    todo = get_object_or_404(Todo, pk=pk, student_id=request.user.id)
    todo.is_done = not todo.is_done
    todo.save(update_fields=["is_done"])
    return _redirect_to_day(todo.due_date.isoformat())


@student_required
@require_POST
def todo_edit(request, pk):
    todo = get_object_or_404(Todo, pk=pk, student_id=request.user.id)
    content = (request.POST.get("content") or "").strip()
    if content:
        todo.content = content[:500]
        todo.save(update_fields=["content"])
    return _redirect_to_day(todo.due_date.isoformat())


@student_required
@require_POST
def todo_delete(request, pk):
    todo = Todo.objects.filter(pk=pk, student_id=request.user.id).first()
    day = todo.due_date.isoformat() if todo else None
    if todo:
        todo.delete()
    return _redirect_to_day(day)
