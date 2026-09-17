"""학생 과제 목록 — 탭(해야 할/제출한/피드백)·유형 필터·검색·정렬.

2조 원본(feat/student-list-sort, feat/submission-link-guidance 일부)의 UI 개편 중
탭/검색/정렬 로직만 선택 반영한 것에 대한 회귀 테스트. GitHub 링크 제출 차단 정책은
여전히 보류 상태이므로 그와 관련된 테스트는 포함하지 않는다
(test_preserved_link_policy.py 참고).
"""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from lms_modules.core.models import Assignment, Submission


class AssignmentListTests(TestCase):
    databases = {"default", "assignment_lms"}

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            approval_status="approved", is_active=True, is_onboarded=True,
            email="assignment-list-student@example.com",
        )
        self.client.force_login(self.user)
        self._patches = []
        for target, val in [
            ("lms_modules.student.views_submit.accounts.is_student", True),
            ("lms_modules.student.views_submit.accounts.get_user_team", None),
            ("lms_modules.student.views_submit.external_student_id", self.user.id),
            ("lms_modules.common.context_processors.accounts.is_tutor", False),
            ("lms_modules.common.context_processors.accounts.is_student", True),
        ]:
            p = patch(target, return_value=val)
            p.start()
            self.addCleanup(p.stop)

    def _assignment(self, title, **overrides):
        values = {
            "title": title,
            "due_at": timezone.now() + timedelta(days=3),
            "created_by": 1,
            "is_team": False,
        }
        values.update(overrides)
        return Assignment.objects.create(**values)

    def _get(self, **params):
        return self.client.get(reverse("lms:student:assignment-list"), params)

    def test_filters_by_status_tab(self):
        submitted_assignment = self._assignment(title="제출한 과제")
        self._assignment(title="미제출 과제")
        Submission.objects.create(
            assignment=submitted_assignment, student_id=self.user.id
        )

        response = self._get(status="submitted")

        self.assertContains(response, "제출한 과제")
        self.assertNotContains(response, "미제출 과제")

    def test_todo_tab_excludes_closed_assignments_from_main_list(self):
        self._assignment(title="진행 중 미제출")
        self._assignment(
            title="마감된 미제출",
            due_at=timezone.now() - timedelta(days=1),
            allow_late=False,
        )

        response = self._get(status="todo")

        self.assertContains(response, "진행 중 미제출")
        # "해야 할 과제" 메인 목록(rows)에는 안 들어간다 — 대신 "마감된 과제" 섹션에 별도 표시된다
        # (test_closed_unsubmitted_assignment_* 참고). 페이지 전체에서 사라지는 게 아니다.
        main_titles = [row["assignment"].title for row in response.context["rows"]]
        self.assertNotIn("마감된 미제출", main_titles)

    def test_sorts_todo_assignments_by_nearest_deadline(self):
        now = timezone.now()
        older_open = self._assignment(
            title="먼저 생성된 진행 과제", due_at=now + timedelta(days=3)
        )
        recent_open = self._assignment(
            title="최근 생성된 진행 과제", due_at=now + timedelta(days=1)
        )

        response = self._get(status="todo")

        assignment_ids = [
            row["assignment"].id for row in response.context["rows"]
        ]
        # 기본 정렬(마감 임박순)은 생성 시각과 무관하게 마감이 가까운 순.
        self.assertEqual(assignment_ids, [recent_open.id, older_open.id])

    def test_filters_by_assignment_type(self):
        self._assignment(title="개인 과제", is_team=False)
        self._assignment(title="팀 전용 과제", is_team=True)

        response = self._get(status="todo", type="team")

        self.assertContains(response, "팀 전용 과제")
        self.assertNotContains(response, '<h3 class="assignment-title">개인 과제</h3>')

    def test_searches_by_title(self):
        self._assignment(title="파이썬 기초 과제")
        self._assignment(title="데이터베이스 과제")

        response = self._get(status="todo", q="파이썬")

        self.assertContains(response, "파이썬 기초 과제")
        self.assertNotContains(response, "데이터베이스 과제")
        self.assertEqual(response.context["search_query"], "파이썬")

    def test_counts_each_status(self):
        self._assignment(title="해야 할 과제")
        submitted = self._assignment(title="제출한 과제")
        feedback = self._assignment(title="피드백 과제")
        Submission.objects.create(assignment=submitted, student_id=self.user.id)
        Submission.objects.create(
            assignment=feedback, student_id=self.user.id, final_score=95
        )

        response = self._get()

        self.assertEqual(
            response.context["status_counts"],
            {"todo": 1, "submitted": 1, "feedback": 1},
        )

    def test_late_available_assignment_appears_in_collapsible_section(self):
        self._assignment(
            title="지각 제출 가능 과제",
            due_at=timezone.now() - timedelta(days=1),
            allow_late=True,
        )

        response = self._get(status="todo")

        self.assertEqual(len(response.context["late_rows"]), 1)
        self.assertContains(response, "지각제출 허용")
        self.assertContains(response, "지각 제출 가능 과제")
        # 지각 제출 가능 과제는 "마감된 과제"(제출 불가) 섹션과는 겹치지 않는다.
        self.assertEqual(len(response.context["closed_rows"]), 0)

    # ---------- 마감 + 지각 불가 + 미제출 (allow_late=False) ----------

    def test_closed_unsubmitted_assignment_appears_in_closed_section(self):
        self._assignment(
            title="마감된 미제출 과제",
            due_at=timezone.now() - timedelta(days=1),
            allow_late=False,
        )

        response = self._get(status="todo")

        self.assertEqual(len(response.context["closed_rows"]), 1)
        self.assertContains(response, "마감된 과제")
        self.assertContains(response, "마감된 미제출 과제")

    def test_closed_assignment_has_no_submit_action(self):
        assignment = self._assignment(
            title="마감된 미제출 과제",
            due_at=timezone.now() - timedelta(days=1),
            allow_late=False,
        )

        response = self._get(status="todo")

        row = response.context["closed_rows"][0]
        self.assertFalse(row["can_submit"])
        submit_url = reverse("lms:student:assignment-submit", args=[assignment.id])
        self.assertNotContains(response, f'href="{submit_url}"')
        self.assertNotContains(response, f'data-href="{submit_url}"')

    def test_closed_assignment_shows_closed_state_label(self):
        self._assignment(
            title="마감된 미제출 과제",
            due_at=timezone.now() - timedelta(days=1),
            allow_late=False,
        )

        response = self._get(status="todo")

        self.assertContains(response, '<span class="assignment-state is-closed">마감</span>')
        self.assertContains(response, "제출 기한이 지나 더 이상 제출할 수 없습니다.")

    def test_submitted_and_feedback_tabs_unaffected_by_closed_section(self):
        # 마감+미제출 과제가 새로 추가돼도 이미 제출/피드백된 과제의 탭 동작은 그대로다.
        submitted = self._assignment(title="제출한 과제")
        feedback = self._assignment(title="피드백 과제")
        Submission.objects.create(assignment=submitted, student_id=self.user.id)
        Submission.objects.create(
            assignment=feedback, student_id=self.user.id, final_score=95
        )
        self._assignment(
            title="마감된 미제출 과제",
            due_at=timezone.now() - timedelta(days=1),
            allow_late=False,
        )

        submitted_response = self._get(status="submitted")
        self.assertContains(submitted_response, "제출한 과제")
        self.assertNotContains(submitted_response, "마감된 미제출 과제")

        feedback_response = self._get(status="feedback")
        self.assertContains(feedback_response, "피드백 과제")
        self.assertNotContains(feedback_response, "마감된 미제출 과제")
