from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from PIL import Image

from accounts.models import User
from bug_reports.forms import ReportForm
from bug_reports.models import BugReport


def capture():
    data = BytesIO()
    Image.new("RGB", (20, 20), "white").save(data, format="PNG")
    return SimpleUploadedFile("capture.png", data.getvalue(), content_type="image/png")


class BugReportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = User.objects.create_user(
            email="owner@example.com", role="student", approval_status="approved", is_onboarded=True
        )
        cls.other = User.objects.create_user(
            email="other@example.com", role="student", approval_status="approved", is_onboarded=True
        )
        cls.tutor = User.objects.create_user(
            email="tutor@example.com", role="tutor", approval_status="approved", is_onboarded=True
        )
        cls.report = BugReport.objects.create(
            reporter=cls.owner, title="저장 오류", description="저장 실패"
        )

    def login(self, user):
        self.client.force_login(user, backend="django.contrib.auth.backends.ModelBackend")
        session = self.client.session
        session["auth_session_version"] = user.auth_session_version
        session.save()

    def test_anonymous_redirected(self):
        for url in (
            "/bug-reports/",
            "/bug-reports/new/",
            f"/bug-reports/{self.report.pk}/",
            f"/bug-reports/{self.report.pk}/screenshot/",
        ):
            self.assertEqual(self.client.get(url).status_code, 302)

    def test_create_image_report_and_download(self):
        self.login(self.owner)
        result = self.client.post(
            reverse("bug_reports:create"),
            {
                "title": "화면 오류",
                "description": "저장 버튼을 누르면 오류",
                "page_url": "http://localhost:8000/results/?token=secret#detail",
                "screenshot": capture(),
                "status": "resolved",
                "reporter": self.other.pk,
            },
        )
        report = BugReport.objects.exclude(pk=self.report.pk).get()
        self.assertRedirects(result, reverse("bug_reports:detail", args=[report.pk]))
        self.assertEqual(report.reporter, self.owner)
        self.assertEqual(report.status, "open")
        self.assertEqual(report.page_url, "http://localhost:8000/results/")
        download = self.client.get(reverse("bug_reports:screenshot", args=[report.pk]))
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download["Cache-Control"], "private, no-store")
        self.assertTrue(b"".join(download.streaming_content).startswith(b"\x89PNG"))
        report.screenshot.delete(save=False)

    def test_other_student_cannot_read_or_download(self):
        self.login(self.other)
        self.assertNotContains(self.client.get(reverse("bug_reports:index")), self.report.title)
        for name in ("detail", "screenshot"):
            self.assertEqual(
                self.client.get(reverse("bug_reports:" + name, args=[self.report.pk])).status_code,
                404,
            )

    def test_owner_cannot_change_status(self):
        self.login(self.owner)
        self.assertEqual(
            self.client.post(
                reverse("bug_reports:detail", args=[self.report.pk]),
                {"status": "resolved", "response": "変更"},
            ).status_code,
            403,
        )
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "open")

    def test_tutor_can_resolve_and_owner_sees_only_status(self):
        self.login(self.tutor)
        self.assertContains(self.client.get(reverse("bug_reports:index")), self.report.title)
        result = self.client.post(
            reverse("bug_reports:detail", args=[self.report.pk]),
            {"status": "resolved"},
        )
        self.assertEqual(result.status_code, 302)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "resolved")
        self.assertEqual(self.report.updated_by, self.tutor)
        self.login(self.owner)
        detail = self.client.get(reverse("bug_reports:detail", args=[self.report.pk]))
        self.assertContains(detail, "해결 완료")
        self.assertNotContains(detail, "처리 답변")
        self.assertNotContains(detail, "처리 상태 변경")

    def test_owner_sees_open_report_as_received(self):
        self.login(self.owner)
        self.assertContains(
            self.client.get(reverse("bug_reports:detail", args=[self.report.pk])), "접수 완료"
        )

    def test_invalid_status_rejected(self):
        self.login(self.tutor)
        result = self.client.post(
            reverse("bug_reports:detail", args=[self.report.pk]), {"status": "bogus"}
        )
        self.assertEqual(result.status_code, 200)
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, "open")

    def test_detail_embeds_authorized_screenshot(self):
        self.report.screenshot = capture()
        self.report.save()
        self.login(self.owner)
        screenshot_url = reverse("bug_reports:screenshot", args=[self.report.pk])
        detail = self.client.get(reverse("bug_reports:detail", args=[self.report.pk]))
        self.assertContains(detail, f'src="{screenshot_url}"')
        self.assertContains(detail, "첨부된 캡처")
        self.report.screenshot.delete(save=False)

    def test_blank_fields_rejected(self):
        form = ReportForm({"title": "   ", "description": "  "})
        self.assertFalse(form.is_valid())

    def test_fake_image_rejected(self):
        form = ReportForm(
            {"title": "오류", "description": "내용"},
            {
                "screenshot": SimpleUploadedFile(
                    "fake.png", b"<script>alert(1)</script>", content_type="image/png"
                )
            },
        )
        self.assertFalse(form.is_valid())
        self.assertIn("screenshot", form.errors)

    def test_large_image_file_rejected(self):
        upload = capture()
        upload.size = 5 * 1024 * 1024 + 1
        form = ReportForm({"title": "오류", "description": "내용"}, {"screenshot": upload})
        self.assertFalse(form.is_valid())
        self.assertIn("screenshot", form.errors)

    def test_script_url_rejected_and_content_escaped(self):
        form = ReportForm(
            {"title": "오류", "description": "내용", "page_url": "javascript:alert(1)"}
        )
        self.assertFalse(form.is_valid())
        self.report.description = "<script>alert(1)</script>"
        self.report.save()
        self.login(self.owner)
        result = self.client.get(reverse("bug_reports:detail", args=[self.report.pk]))
        self.assertContains(result, "&lt;script&gt;")

    def test_post_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner, backend="django.contrib.auth.backends.ModelBackend")
        session = client.session
        session["auth_session_version"] = self.owner.auth_session_version
        session.save()
        self.assertEqual(
            client.post(
                reverse("bug_reports:create"), {"title": "오류", "description": "내용"}
            ).status_code,
            403,
        )

    def test_form_and_filter_render(self):
        self.login(self.owner)
        self.assertContains(self.client.get(reverse("bug_reports:create")), "신고 접수하기")
        self.assertNotContains(
            self.client.get(reverse("bug_reports:index"), {"status": "resolved"}), self.report.title
        )

    def test_profile_menu_links_to_report_history(self):
        self.login(self.owner)
        result = self.client.get(reverse("accounts:mypage"))
        self.assertContains(result, f'href="{reverse("bug_reports:index")}"')
