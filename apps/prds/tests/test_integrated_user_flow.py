import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from apps.integration.repository import FixtureIntegrationRepository
from apps.prds.models import PrdTemplate, PrdTemplateQuestion, PrdTemplateSection


class IntegratedIdeaDeveloperUserFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="idea-flow@example.com",
            password="test-password",
            role=User.Role.STUDENT,
            approval_status=User.ApprovalStatus.APPROVED,
            is_onboarded=True,
        )
        self.repository = FixtureIntegrationRepository(
            users=(
                {
                    "user_id": self.user.pk,
                    "role": "student",
                    "approval_status": "approved",
                    "is_active": True,
                    "is_staff": False,
                    "is_superuser": False,
                    "user_email": self.user.email,
                    "primary_email": self.user.email,
                    "display_name_snapshot": "통합 테스트 사용자",
                    "first_name": "",
                    "last_name": "",
                },
            ),
            memberships=(),
            active_statuses=("in_progress",),
        )
        self.repository_patch = patch(
            "apps.prds.views.get_default_integration_repository",
            return_value=self.repository,
        )
        self.repository_patch.start()
        self.addCleanup(self.repository_patch.stop)
        template, _ = PrdTemplate.objects.update_or_create(
            prd_type="new_product",
            defaults={"name": "통합 테스트"},
        )
        section, _ = PrdTemplateSection.objects.update_or_create(
            template=template,
            position=1,
            defaults={
                "title": "프로젝트 요약",
                "guide": "통합 흐름을 검증합니다.",
            },
        )
        PrdTemplateQuestion.objects.update_or_create(
            section=section,
            position=1,
            defaults={"prompt": "프로젝트 이름은 무엇인가요?"},
        )
        self.client.force_login(self.user)

    def request_json(self, method, url, payload=None, **headers):
        response = getattr(self.client, method)(
            url,
            data=json.dumps(payload or {}),
            content_type="application/json",
            headers=headers,
        )
        return response, response.json()

    def test_create_write_comment_and_brainstorm_flow(self):
        create_url = reverse("prd_api:create")
        create_payload = {
            "prd_type": "new_product",
            "title": "통합 사용자 흐름 검증",
            "description": "생성부터 브레인스토밍까지 검증합니다.",
            "deadline": None,
            "participant_user_ids": [],
        }

        created_response, created_body = self.request_json(
            "post",
            create_url,
            create_payload,
            **{"Idempotency-Key": "integrated-flow-create"},
        )
        self.assertEqual(created_response.status_code, 201, created_body)
        self.assertTrue(created_body["ok"])
        prd_id = created_body["data"]["prd"]["id"]

        repeated_response, repeated_body = self.request_json(
            "post",
            create_url,
            create_payload,
            **{"Idempotency-Key": "integrated-flow-create"},
        )
        self.assertEqual(repeated_response.status_code, 200)
        self.assertFalse(repeated_body["data"]["created"])
        self.assertEqual(repeated_body["data"]["prd"]["id"], prd_id)

        detail_url = reverse("prd_api:detail", args=[prd_id])
        detail_response = self.client.get(detail_url)
        detail_body = detail_response.json()
        self.assertEqual(detail_response.status_code, 200)
        self.assertTrue(detail_body["data"]["sections"])
        question = detail_body["data"]["sections"][0]["questions"][0]

        answer_url = reverse("prd_api:question-answer", args=[prd_id, question["id"]])
        answer_response, answer_body = self.request_json(
            "patch",
            answer_url,
            {
                "content": "사용자 입력이 API와 DB를 거쳐 저장됩니다.",
                "version": question["version"],
            },
        )
        self.assertEqual(answer_response.status_code, 200)
        self.assertEqual(
            answer_body["data"]["answer"]["content"],
            "사용자 입력이 API와 DB를 거쳐 저장됩니다.",
        )

        conflict_response, conflict_body = self.request_json(
            "patch",
            answer_url,
            {"content": "오래된 화면의 입력", "version": question["version"]},
        )
        self.assertEqual(conflict_response.status_code, 409)
        self.assertEqual(conflict_body["error"]["code"], "version_conflict")

        comments_url = reverse("prd_api:comments", args=[prd_id])
        comment_response, comment_body = self.request_json(
            "post",
            comments_url,
            {"content": "통합 코멘트 저장 확인"},
        )
        self.assertEqual(comment_response.status_code, 201)
        self.assertEqual(comment_body["data"]["content"], "통합 코멘트 저장 확인")
        self.assertEqual(
            self.client.get(comments_url).json()["data"]["pagination"]["total_items"], 1
        )

        canvas_url = reverse("brainstorm_api:canvas", args=[prd_id])
        canvas_response = self.client.get(
            canvas_url,
            headers={"Idempotency-Key": "integrated-flow-canvas"},
        )
        canvas_body = canvas_response.json()
        self.assertEqual(canvas_response.status_code, 200, canvas_body)
        self.assertTrue(canvas_body["data"]["canvas"]["created"])

        node_url = reverse("brainstorm_api:node-create", args=[prd_id])
        node_response, node_body = self.request_json(
            "post",
            node_url,
            {"content": "브레인스토밍 메모 저장 확인", "color": "yellow", "x": 120, "y": 90},
            **{"Idempotency-Key": "integrated-flow-note"},
        )
        self.assertEqual(node_response.status_code, 201)
        self.assertEqual(node_body["data"]["content"], "브레인스토밍 메모 저장 확인")

        refreshed_canvas = self.client.get(canvas_url).json()["data"]
        self.assertIn(
            "브레인스토밍 메모 저장 확인",
            {node["content"] for node in refreshed_canvas["nodes"]},
        )

        write_page = self.client.get(reverse("idea-prd-write", args=[prd_id]))
        brainstorm_page = self.client.get(reverse("idea-brainstorm", args=[prd_id]))
        self.assertContains(write_page, 'id="app-shell"')
        self.assertContains(brainstorm_page, 'id="brainstorm-root"')
