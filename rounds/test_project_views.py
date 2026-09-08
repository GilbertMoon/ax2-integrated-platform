from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from django.utils import timezone

from rounds.models import EvaluationRound, ProjectInfo, QuestionTemplate

User = get_user_model()


class ProjectRoundUrlTests(SimpleTestCase):
    def test_project_round_is_manage_rounds(self):
        self.assertEqual(reverse("rounds:project-list"), "/manage/rounds/")

    def test_project_round_detail_is_under_manage_rounds(self):
        self.assertEqual(
            reverse("rounds:project-detail", kwargs={"project_id": 10}), "/manage/rounds/10/"
        )

    def test_evaluation_round_list_is_separate(self):
        self.assertEqual(reverse("rounds:list"), "/manage/evaluation-rounds/")

    def test_evaluation_round_create_is_separate(self):
        self.assertEqual(reverse("rounds:create"), "/manage/evaluation-rounds/new/")

    def test_evaluation_round_edit_is_separate(self):
        self.assertEqual(
            reverse("rounds:edit", kwargs={"round_id": 10}), "/manage/evaluation-rounds/10/"
        )


class ProjectViewRenderTests(TestCase):
    """project_* 뷰가 예외 없이 정상 렌더되는지 확인하는 스모크 테스트.

    URL reverse() 검증만으로는 템플릿 렌더 단계의 문제(코드펜스 오염,
    존재하지 않는 폼 필드 참조 등)를 잡을 수 없어서 추가한다.
    """

    def setUp(self):
        self.tutor = User.objects.create_user(
            email="project-tutor@example.com",
            password="strong-test-password",
            first_name="운영튜터",
            role=User.Role.TUTOR,
            approval_status=User.ApprovalStatus.APPROVED,
        )
        self.client.force_login(self.tutor)

        self.team_template = QuestionTemplate.objects.create(
            name="팀 평가", category="TEAM", created_by=self.tutor
        )
        self.peer_template = QuestionTemplate.objects.create(
            name="개인 평가", category="PEER", created_by=self.tutor
        )

        now = timezone.now()

        self.draft_round = EvaluationRound.objects.create(
            title="프로젝트 뷰 테스트용 회차",
            evaluation_start_at=now,
            evaluation_end_at=now + timedelta(days=7),
            target_team_count=2,
            team_template=self.team_template,
            peer_template=self.peer_template,
            created_by=self.tutor,
        )

        self.project_info = ProjectInfo.objects.create(
            name="테스트 프로젝트",
            description="스모크 테스트용 프로젝트",
            evaluationround=self.draft_round,
        )

    def test_project_list_renders(self):
        response = self.client.get(reverse("rounds:project-list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "테스트 프로젝트")

    def test_project_list_does_not_leak_markdown_fence(self):
        response = self.client.get(reverse("rounds:project-list"))
        self.assertNotContains(response, "```html")

    def test_project_detail_renders(self):
        response = self.client.get(
            reverse("rounds:project-detail", kwargs={"project_id": self.project_info.pk})
        )
        self.assertEqual(response.status_code, 200)

    def test_project_create_get_renders(self):
        response = self.client.get(reverse("rounds:project-create"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "```html")

    def test_project_edit_renders_for_draft_round(self):
        response = self.client.get(
            reverse("rounds:project-edit", kwargs={"project_id": self.project_info.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "프로젝트 및 평가 회차 저장")

    def test_project_edit_renders_read_only_for_started_round(self):
        self.draft_round.status = EvaluationRound.Status.IN_PROGRESS
        self.draft_round.started_at = timezone.now()
        self.draft_round.save(update_fields=["status", "started_at"])

        response = self.client.get(
            reverse("rounds:project-edit", kwargs={"project_id": self.project_info.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "수정할 수 없습니다")
        self.assertNotContains(response, "프로젝트 및 평가 회차 저장")


class EvaluationRoundEditRenderTests(TestCase):
    """round_edit(신규/수정) 뷰의 GET 렌더를 확인한다."""

    def setUp(self):
        self.tutor = User.objects.create_user(
            email="round-edit-tutor@example.com",
            password="strong-test-password",
            first_name="회차튜터",
            role=User.Role.TUTOR,
            approval_status=User.ApprovalStatus.APPROVED,
        )
        self.client.force_login(self.tutor)

    def test_round_create_get_renders(self):
        response = self.client.get(reverse("rounds:create"))
        self.assertEqual(response.status_code, 200)

    def test_round_edit_get_renders_for_draft_round(self):
        now = timezone.now()
        round_obj = EvaluationRound.objects.create(
            title="회차 수정 테스트",
            evaluation_start_at=now,
            evaluation_end_at=now + timedelta(days=7),
            target_team_count=2,
            created_by=self.tutor,
        )

        response = self.client.get(reverse("rounds:edit", kwargs={"round_id": round_obj.pk}))
        self.assertEqual(response.status_code, 200)
