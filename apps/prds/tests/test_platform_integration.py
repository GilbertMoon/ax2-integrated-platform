from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from apps.integration.context import UserAttributeExternalIdMapper


class IdeaDeveloperPlatformIntegrationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="idea-integration@example.com",
            password="test-password",
            role=User.Role.STUDENT,
            approval_status=User.ApprovalStatus.APPROVED,
            is_onboarded=True,
        )

    def test_core_user_pk_is_used_as_idea_external_user_id(self):
        self.assertEqual(UserAttributeExternalIdMapper().map(self.user), self.user.pk)

    def test_idea_home_uses_core_login_and_namespaced_template(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("ideas:home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "idea/prds/home.html")
        self.assertContains(response, "Idea Developer")

    def test_idea_routes_are_mounted_in_integrated_urlconf(self):
        self.assertEqual(reverse("ideas:home"), "/ideas/")
        self.assertEqual(reverse("prd_api:create"), "/api/v1/prds/")
        self.assertEqual(
            reverse("ai_api:conversation", args=[7]),
            "/api/v1/prds/7/ai/conversation/",
        )
        self.assertEqual(
            reverse("brainstorm_api:canvas", args=[7]),
            "/api/v1/prds/7/brainstorm/canvas/",
        )
