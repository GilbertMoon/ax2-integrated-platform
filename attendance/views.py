# ============================================================
# attendance/views.py
# 화면 뷰(attendance_board)와 JSON API(me / user / update)를 함께 둔다.
# teams/views.py, rounds/views.py와 동일한 스타일:
#   - 함수형 뷰
#   - 화면: @login_required + _require_operations + render()
#   - API: JsonResponse + require_GET/POST
# 권한은 accounts/permissions.py의 검증된 함수를 그대로 쓴다.
# ============================================================

import json
from datetime import date as date_cls

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from accounts.permissions import is_operations_user, is_student_user
from attendance.models import AttendanceRecord
from attendance.services import attendance_board_rows, save_attendance_board

User = get_user_model()


def _require_operations(user):
    if not is_operations_user(user):
        raise PermissionDenied


def _error_response(code: str, message: str, status: int) -> JsonResponse:
    return JsonResponse({"error": {"code": code, "message": message}}, status=status)


def _parse_day(raw: str | None):
    if raw:
        parsed = parse_date(raw)
        if parsed is not None:
            return parsed
    return date_cls.today()


# ------------------------------------------------------------
# 화면 (사이드바 "근태")
# ------------------------------------------------------------


@login_required
@require_http_methods(["GET", "POST"])
def attendance_board(request: HttpRequest):
    """날짜별 수강생 출결 조회·입력. 튜터·관리자 전용."""
    _require_operations(request.user)

    if request.method == "POST":
        day = _parse_day(request.POST.get("date"))
        status_by_user: dict[int, str] = {}
        for key, value in request.POST.items():
            if not key.startswith("status_"):
                continue
            try:
                user_id = int(key.removeprefix("status_"))
            except ValueError:
                continue
            status_by_user[user_id] = value
        changed = save_attendance_board(day, status_by_user)
        messages.success(request, f"{day} 근태를 저장했습니다. (반영 {changed}명)")
        return redirect(f"{reverse('attendance:board')}?date={day.isoformat()}")

    day = _parse_day(request.GET.get("date"))
    rows = attendance_board_rows(day)
    summary = {
        "present": sum(1 for row in rows if row["status"] == "present"),
        "late": sum(1 for row in rows if row["status"] == "late"),
        "absent": sum(1 for row in rows if row["status"] == "absent"),
        "blank": sum(1 for row in rows if not row["status"]),
    }
    return render(
        request,
        "attendance/board.html",
        {
            "day": day,
            "rows": rows,
            "summary": summary,
            "statuses": AttendanceRecord.Status.choices,
        },
    )


# ------------------------------------------------------------
# JSON API
# ------------------------------------------------------------


@require_GET
def my_attendance_view(request: HttpRequest) -> JsonResponse:
    """로그인한 본인의 근태 기록 조회. 학생 또는 튜터 본인 확인용."""
    if not (is_student_user(request.user) or is_operations_user(request.user)):
        return _error_response("permission_denied", "permission denied", 403)

    records = AttendanceRecord.objects.filter(user_id=request.user.id).values(
        "date", "status", "checked_by_face_recognition"
    )
    return JsonResponse({"user_id": request.user.id, "records": list(records)})


@require_GET
def user_attendance_view(request: HttpRequest, user_id: int) -> JsonResponse:
    """특정 사용자(accounts_user.id)의 근태 조회. 튜터(운영자) 전용."""
    if not is_operations_user(request.user):
        return _error_response("permission_denied", "permission denied", 403)

    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return _error_response("not_found", "해당 사용자를 찾을 수 없습니다.", 404)

    records = AttendanceRecord.objects.filter(user_id=user_id).values(
        "date", "status", "checked_by_face_recognition"
    )
    return JsonResponse(
        {
            "user_id": target_user.id,
            # User.__str__와 동일한 패턴: first_name이 없으면 email로 대체
            "display_name": target_user.first_name or target_user.email,
            "records": list(records),
        }
    )


@require_POST
def update_attendance_view(request: HttpRequest) -> JsonResponse:
    """근태 기록 생성/수정. 튜터(운영자) 전용.
    body 예시: {"user_id": 5, "date": "2026-09-01", "status": "present"}
    """
    if not is_operations_user(request.user):
        return _error_response("permission_denied", "permission denied", 403)

    try:
        payload = json.loads(request.body or b"{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _error_response("invalid_request", "request body must be valid JSON", 400)
    if not isinstance(payload, dict):
        return _error_response("invalid_request", "request body must be a JSON object", 400)

    user_id = payload.get("user_id")
    date = payload.get("date")
    status = payload.get("status")

    if not all([user_id, date, status]):
        return _error_response("invalid_request", "user_id, date, status는 필수입니다.", 400)

    if parse_date(str(date)) is None:
        return _error_response("invalid_request", "date는 YYYY-MM-DD 형식이어야 합니다.", 400)

    if status not in AttendanceRecord.Status.values:
        return _error_response(
            "invalid_request", f"status는 {AttendanceRecord.Status.values} 중 하나여야 합니다.", 400
        )

    if not User.objects.filter(id=user_id).exists():
        return _error_response("not_found", "해당 사용자를 찾을 수 없습니다.", 404)

    record, _created = AttendanceRecord.objects.update_or_create(
        user_id=user_id,
        date=date,
        defaults={"status": status},
    )
    return JsonResponse(
        {"user_id": record.user_id, "date": str(record.date), "status": record.status}
    )


@login_required
def kiosk_page(request):
    """
    교실 태블릿에 띄워둘 키오스크 화면.
    튜터 계정으로 로그인한 상태에서 이 페이지를 열어두면,
    학생들이 차례로 와서 촬영 버튼만 누르면 됩니다.
    """
    if not is_operations_user(request.user):
        raise PermissionDenied
    return render(request, "attendance/kiosk.html")


@require_POST
def face_checkin_view(request: HttpRequest) -> JsonResponse:
    """
    얼굴 사진을 업로드받아 출석을 자동 기록한다.
    호출 예: POST /attendance/face-checkin/  (multipart/form-data, "image" 필드에 사진)
    """
    if not is_operations_user(request.user):
        return JsonResponse(
            {"error": {"code": "permission_denied", "message": "permission denied"}}, status=403
        )

    image_file = request.FILES.get("image")
    if image_file is None:
        return JsonResponse(
            {"error": {"code": "invalid_request", "message": "image 파일이 필요합니다."}},
            status=400,
        )

    from attendance.face_services import record_face_checkin

    result = record_face_checkin(image_file)
    return JsonResponse(result)
