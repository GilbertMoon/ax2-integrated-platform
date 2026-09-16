"""회차 마감 결과 화면/CSV — RoundScore는 전체 학생 기준으로 저장되지만
(grading.snapshot, 변경 없음) 화면·CSV는 그 회차의 실제 참가자만 보여줘야 한다.
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from lms_modules.tutor.models import RoundScore

ROUND_ID = 900


@override_settings(DEV_SKIP_AUTH=True)
class RoundCloseParticipantFilterTests(TestCase):
    databases = {"default", "assignment_lms"}

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            approval_status="approved", is_active=True, is_onboarded=True,
            email="round-close-tutor@example.com",
        )
        self.client.force_login(self.user)
        for target, val in [
            ("lms_modules.tutor.views_round.accounts.is_tutor", True),
            # 전체 활성 학생 3명(11,12,13) 중 이 회차 참가자는 2명(11,12) — 13은 비참가자.
            ("lms_modules.tutor.views_round.accounts.get_round_participant_ids", {11, 12}),
        ]:
            p = patch(target, return_value=val)
            p.start()
            self.addCleanup(p.stop)

        for sid, name in [(11, "학생11"), (12, "학생12"), (13, "학생13")]:
            RoundScore.objects.create(
                round_id=ROUND_ID,
                round_title="테스트 회차",
                student_id=sid,
                student_name=name,
                total=80.0,
                achievement=80.0,
                sincerity=100.0,
                team_included=True,
                assignment_ids=[1, 2],
                closed_at=timezone.now(),
                closed_by=1,
            )

    def test_round_score_has_all_three_students(self):
        # 전제 확인: snapshot()이 저장하는 행 자체는(이 테스트는 직접 생성했지만) 3건 그대로.
        self.assertEqual(RoundScore.objects.filter(round_id=ROUND_ID).count(), 3)

    def test_result_page_shows_only_round_participants(self):
        response = self.client.get(
            reverse("lms:tutor:round-close-result", args=[ROUND_ID])
        )
        self.assertEqual(response.status_code, 200)
        shown_ids = {row.student_id for row in response.context["rows"]}
        self.assertEqual(shown_ids, {11, 12})
        self.assertContains(response, "학생11")
        self.assertContains(response, "학생12")
        self.assertNotContains(response, "학생13")

    def test_csv_includes_only_round_participants(self):
        response = self.client.get(
            reverse("lms:tutor:round-close-csv", args=[ROUND_ID])
        )
        content = response.content.decode("utf-8-sig")
        self.assertIn("학생11", content)
        self.assertIn("학생12", content)
        self.assertNotIn("학생13", content)

    def test_viewing_result_does_not_delete_non_participant_round_score(self):
        self.client.get(reverse("lms:tutor:round-close-result", args=[ROUND_ID]))
        self.client.get(reverse("lms:tutor:round-close-csv", args=[ROUND_ID]))
        # 비참가자(13) 행도 DB에는 그대로 남아 있어야 한다 — 화면/CSV에서만 제외.
        self.assertEqual(RoundScore.objects.filter(round_id=ROUND_ID).count(), 3)
        self.assertTrue(
            RoundScore.objects.filter(round_id=ROUND_ID, student_id=13).exists()
        )
