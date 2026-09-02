from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from attendance.models import AttendanceRecord
from attendance.services import approved_students, attendance_board_rows, save_attendance_board


def _make_tutor(email="tutor@ax.com", **extra):
    defaults = {
        "password": "strong-test-password",
        "first_name": "튜터",
        "role": User.Role.TUTOR,
        "approval_status": User.ApprovalStatus.APPROVED,
        "is_active": True,
    }
    defaults.update(extra)
    return User.objects.create_user(email=email, **defaults)


def _make_student(email, first_name="학생", **extra):
    defaults = {
        "password": "strong-test-password",
        "first_name": first_name,
        "role": User.Role.STUDENT,
        "approval_status": User.ApprovalStatus.APPROVED,
        "is_active": True,
    }
    defaults.update(extra)
    return User.objects.create_user(email=email, **defaults)


class ApprovedStudentsTests(TestCase):
    """근태 대상(approved_students)에 포함되면 안 되는 케이스를 명시적으로 검증한다."""

    def test_only_approved_active_students_are_included(self):
        approved = _make_student("approved@example.com")
        _make_student("pending@example.com", approval_status=User.ApprovalStatus.PENDING)
        _make_student("inactive@example.com", is_active=False)
        _make_tutor("other-tutor@example.com")

        result = list(approved_students())

        self.assertEqual(result, [approved])


class AttendanceBoardRowsTests(TestCase):
    def setUp(self):
        self.day = "2026-09-01"
        self.student = _make_student("board-student@example.com", first_name="김학생")

    def test_row_without_record_has_blank_status(self):
        rows = attendance_board_rows(self.day)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["status"], "")
        self.assertEqual(rows[0]["display_name"], "김학생")
        self.assertFalse(rows[0]["by_face"])

    def test_row_reflects_existing_record(self):
        AttendanceRecord.objects.create(
            user=self.student, date=self.day, status=AttendanceRecord.Status.LATE
        )

        rows = attendance_board_rows(self.day)

        self.assertEqual(rows[0]["status"], "late")


class SaveAttendanceBoardTests(TestCase):
    def setUp(self):
        self.day = "2026-09-01"
        self.student = _make_student("save-student@example.com")

    def test_saving_a_status_creates_a_record(self):
        changed = save_attendance_board(self.day, {self.student.id: "present"})

        self.assertEqual(changed, 1)
        record = AttendanceRecord.objects.get(user=self.student, date=self.day)
        self.assertEqual(record.status, "present")
        self.assertFalse(record.checked_by_face_recognition)

    def test_manual_save_overrides_face_recognition_flag(self):
        AttendanceRecord.objects.create(
            user=self.student,
            date=self.day,
            status=AttendanceRecord.Status.PRESENT,
            checked_by_face_recognition=True,
        )

        save_attendance_board(self.day, {self.student.id: "late"})

        record = AttendanceRecord.objects.get(user=self.student, date=self.day)
        self.assertEqual(record.status, "late")
        self.assertFalse(record.checked_by_face_recognition)

    def test_blank_status_deletes_existing_record(self):
        AttendanceRecord.objects.create(
            user=self.student, date=self.day, status=AttendanceRecord.Status.ABSENT
        )

        changed = save_attendance_board(self.day, {self.student.id: ""})

        self.assertEqual(changed, 1)
        self.assertFalse(AttendanceRecord.objects.filter(user=self.student, date=self.day).exists())

    def test_unknown_user_id_is_silently_ignored(self):
        changed = save_attendance_board(self.day, {999999: "present"})

        self.assertEqual(changed, 0)

    def test_invalid_status_is_silently_ignored(self):
        changed = save_attendance_board(self.day, {self.student.id: "on_vacation"})

        self.assertEqual(changed, 0)
        self.assertFalse(AttendanceRecord.objects.filter(user=self.student, date=self.day).exists())


class AttendanceBoardViewTests(TestCase):
    """운영 화면(/attendance/): 튜터·관리자만 접근 가능."""

    def setUp(self):
        self.day = "2026-09-01"
        self.tutor = _make_tutor()
        self.student = _make_student("view-student@example.com", first_name="박학생")

    def test_tutor_can_view_board_with_summary(self):
        AttendanceRecord.objects.create(
            user=self.student, date=self.day, status=AttendanceRecord.Status.ABSENT
        )
        self.client.force_login(self.tutor)

        response = self.client.get(reverse("attendance:board"), {"date": self.day})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["summary"]["absent"], 1)
        self.assertContains(response, "박학생")

    def test_student_cannot_view_board(self):
        self.client.force_login(self.student)

        response = self.client.get(reverse("attendance:board"))

        self.assertEqual(response.status_code, 403)

    def test_anonymous_user_is_redirected_to_login(self):
        response = self.client.get(reverse("attendance:board"))

        self.assertNotEqual(response.status_code, 200)

    def test_tutor_post_saves_attendance_and_redirects(self):
        self.client.force_login(self.tutor)

        response = self.client.post(
            reverse("attendance:board"),
            {"date": self.day, f"status_{self.student.id}": "present"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            AttendanceRecord.objects.get(user=self.student, date=self.day).status, "present"
        )

    def test_tutor_post_with_blank_status_removes_record(self):
        AttendanceRecord.objects.create(
            user=self.student, date=self.day, status=AttendanceRecord.Status.PRESENT
        )
        self.client.force_login(self.tutor)

        self.client.post(
            reverse("attendance:board"),
            {"date": self.day, f"status_{self.student.id}": ""},
        )

        self.assertFalse(AttendanceRecord.objects.filter(user=self.student, date=self.day).exists())


class MyAttendanceViewTests(TestCase):
    """/attendance/me/: 학생 본인 또는 튜터·관리자 접근 가능, 본인 기록만 반환."""

    def setUp(self):
        self.day = "2026-09-01"
        self.student = _make_student("me-student@example.com")
        self.other_student = _make_student("me-other@example.com")
        AttendanceRecord.objects.create(
            user=self.student, date=self.day, status=AttendanceRecord.Status.PRESENT
        )
        AttendanceRecord.objects.create(
            user=self.other_student, date=self.day, status=AttendanceRecord.Status.ABSENT
        )

    def test_student_sees_only_own_records(self):
        self.client.force_login(self.student)

        response = self.client.get(reverse("attendance:my-attendance"))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["records"]), 1)
        self.assertEqual(data["records"][0]["status"], "present")

    def test_tutor_can_also_view_my_attendance(self):
        tutor = _make_tutor()
        self.client.force_login(tutor)

        response = self.client.get(reverse("attendance:my-attendance"))

        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_is_denied(self):
        response = self.client.get(reverse("attendance:my-attendance"))

        self.assertEqual(response.status_code, 403)


class UserAttendanceViewTests(TestCase):
    """/attendance/user/<id>/: 튜터·관리자 전용."""

    def setUp(self):
        self.day = "2026-09-01"
        self.tutor = _make_tutor()
        self.student = _make_student("user-view-student@example.com", first_name="이학생")
        AttendanceRecord.objects.create(
            user=self.student, date=self.day, status=AttendanceRecord.Status.LATE
        )

    def test_tutor_can_view_specific_user_attendance(self):
        self.client.force_login(self.tutor)

        response = self.client.get(
            reverse("attendance:user-attendance", kwargs={"user_id": self.student.id})
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["display_name"], "이학생")
        self.assertEqual(len(data["records"]), 1)

    def test_student_cannot_view_other_users_attendance(self):
        self.client.force_login(self.student)

        response = self.client.get(
            reverse("attendance:user-attendance", kwargs={"user_id": self.student.id})
        )

        self.assertEqual(response.status_code, 403)

    def test_returns_404_for_unknown_user(self):
        self.client.force_login(self.tutor)

        response = self.client.get(
            reverse("attendance:user-attendance", kwargs={"user_id": 999999})
        )

        self.assertEqual(response.status_code, 404)


class UpdateAttendanceViewTests(TestCase):
    """/attendance/update/: 튜터·관리자 전용, 방어코드 검증 포함."""

    def setUp(self):
        self.tutor = _make_tutor()
        self.student = _make_student("update-student@example.com")

    def _post_json(self, payload, content_type="application/json"):
        import json

        return self.client.post(
            reverse("attendance:update-attendance"),
            data=json.dumps(payload) if isinstance(payload, dict) else payload,
            content_type=content_type,
        )

    def test_tutor_can_create_and_update_a_record(self):
        self.client.force_login(self.tutor)

        response = self._post_json(
            {"user_id": self.student.id, "date": "2026-09-01", "status": "present"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            AttendanceRecord.objects.get(user=self.student, date="2026-09-01").status, "present"
        )

    def test_student_is_denied(self):
        self.client.force_login(self.student)

        response = self._post_json(
            {"user_id": self.student.id, "date": "2026-09-01", "status": "present"}
        )

        self.assertEqual(response.status_code, 403)

    def test_non_dict_body_returns_400(self):
        self.client.force_login(self.tutor)

        response = self._post_json([1, 2, 3])

        self.assertEqual(response.status_code, 400)

    def test_invalid_json_returns_400(self):
        self.client.force_login(self.tutor)

        response = self.client.post(
            reverse("attendance:update-attendance"),
            data="not-json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)

    def test_missing_field_returns_400(self):
        self.client.force_login(self.tutor)

        response = self._post_json({"user_id": self.student.id, "date": "2026-09-01"})

        self.assertEqual(response.status_code, 400)

    def test_invalid_date_format_returns_400(self):
        self.client.force_login(self.tutor)

        response = self._post_json(
            {"user_id": self.student.id, "date": "2026/09/01", "status": "present"}
        )

        self.assertEqual(response.status_code, 400)

    def test_invalid_status_returns_400(self):
        self.client.force_login(self.tutor)

        response = self._post_json(
            {"user_id": self.student.id, "date": "2026-09-01", "status": "on_vacation"}
        )

        self.assertEqual(response.status_code, 400)

    def test_unknown_user_id_returns_404(self):
        self.client.force_login(self.tutor)

        response = self._post_json({"user_id": 999999, "date": "2026-09-01", "status": "present"})

        self.assertEqual(response.status_code, 404)
