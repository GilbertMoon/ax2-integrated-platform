"""근태 화면이 쓰는 조회·저장 로직. 뷰는 요청 처리만 하고 여기서 DB를 다룬다."""

from accounts.models import User
from attendance.models import AttendanceRecord


def approved_students():
    """근태 대상 = 승인된 활성 수강생."""
    return User.objects.filter(
        role=User.Role.STUDENT,
        approval_status=User.ApprovalStatus.APPROVED,
        is_active=True,
    ).order_by("first_name", "email")


def attendance_board_rows(day):
    """해당 날짜의 수강생별 출결 한 줄씩. 기록이 없으면 status는 빈 문자열."""
    records = {record.user_id: record for record in AttendanceRecord.objects.filter(date=day)}
    rows = []
    for student in approved_students():
        record = records.get(student.id)
        rows.append(
            {
                "user_id": student.id,
                "display_name": student.first_name or student.email,
                "email": student.email,
                "status": record.status if record else "",
                "by_face": record.checked_by_face_recognition if record else False,
            }
        )
    return rows


def save_attendance_board(day, status_by_user):
    """status_by_user: {user_id: 'present'|'late'|'absent'|''}.

    빈 문자열이면 그 날 기록을 지운다(미기록으로 되돌림). 튜터가 직접 저장한 값은
    얼굴인식 자동 기록보다 우선이므로 checked_by_face_recognition을 False로 덮는다.
    유효하지 않은 사용자·상태는 조용히 건너뛴다.
    """
    valid_ids = set(approved_students().values_list("id", flat=True))
    valid_statuses = set(AttendanceRecord.Status.values)
    changed = 0
    for user_id, status in status_by_user.items():
        if user_id not in valid_ids:
            continue
        if status == "":
            deleted, _ = AttendanceRecord.objects.filter(user_id=user_id, date=day).delete()
            changed += bool(deleted)
            continue
        if status not in valid_statuses:
            continue
        AttendanceRecord.objects.update_or_create(
            user_id=user_id,
            date=day,
            defaults={"status": status, "checked_by_face_recognition": False},
        )
        changed += 1
    return changed
