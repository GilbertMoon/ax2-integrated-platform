from django.test import TestCase
from django.urls import reverse

from accounts.models import User


class AuthMeViewTests(TestCase):
    """/api/auth/me/: 로그인 사용자 본인 정보 조회. 미인증 시 로그인 리다이렉트가 아니라 401 JSON."""

    def setUp(self):
        self.url = reverse("api_auth_me")
        self.student = User.objects.create_user(
            email="authme-student@example.com",
            password="strong-test-password",
            first_name="김본인",
            role=User.Role.STUDENT,
            approval_status=User.ApprovalStatus.APPROVED,
        )

    def test_authenticated_user_gets_own_info(self):
        self.client.force_login(self.student)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.student.id)
        self.assertEqual(data["display_name"], "김본인")
        self.assertEqual(data["email"], self.student.email)
        self.assertEqual(data["role"], User.Role.STUDENT)

    def test_anonymous_user_gets_401_json_not_redirect(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "unauthorized")

    def test_post_is_not_allowed(self):
        self.client.force_login(self.student)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 405)
