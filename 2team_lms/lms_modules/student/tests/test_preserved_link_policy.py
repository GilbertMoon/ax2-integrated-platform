"""GitHub 링크 제출 검증 정책 — 2조 develop 최신 정책 반영.

이전에는 이 파일이 "저장소·폴더 링크를 네트워크 검증 없이 허용"하는 보류 상태를
보호했다. 이제 2조 develop과 동일하게 GitHub 단일 파일(blob/raw) 링크만 허용하고,
저장소·폴더(tree)·존재하지 않는/비공개 링크는 제출 시점에 차단한다.

정책의 핵심(임의로 확대하지 말 것):
- "유효성 검증 실패"(not_blob·not_found) → 차단
- "일시적 API 장애/타임아웃"(error) → 통과 (우리 쪽 문제로 학생을 막지 않는다)
- GitHub 링크가 아니면(is_github_url=False) 애초에 검증하지 않는다.
"""
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from lms_modules.core.models import Assignment, Submission


class GithubLinkSubmissionPolicyTests(TestCase):
    databases = {"default", "assignment_lms"}

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            approval_status="approved", is_active=True, is_onboarded=True,
            email="link-policy-student@example.com",
        )
        self.client.force_login(self.user)
        for target, val in [
            ("lms_modules.student.views_submit.accounts.is_student", True),
            ("lms_modules.student.views_submit.accounts.get_user_team", None),
            # 제출 성공 후 리다이렉트되는 assignment_preview 화면이 조회함 (실제 계정 뷰는
            # 이 테스트 DB에 없음 — 다른 tutor 테스트와 동일한 패턴으로 mock).
            ("lms_modules.student.views_submit.accounts.get_user", None),
        ]:
            p = patch(target, return_value=val)
            p.start()
            self.addCleanup(p.stop)
        self.assignment = Assignment.objects.create(
            title="과제", due_at=timezone.now() + timedelta(days=1),
            is_team=False, created_by=1,
        )

    def _submit(self, links):
        return self.client.post(
            reverse("lms:student:assignment-submit", args=[self.assignment.id]),
            {"description": "", "links": links},
        )

    @patch(
        "lms_modules.student.views_submit.github_fetch.probe_github_file",
        return_value="ok",
    )
    def test_valid_blob_link_is_accepted(self, _probe):
        response = self._submit(["https://github.com/example/repo/blob/main/solution.py"])
        self.assertRedirects(
            response, reverse("lms:student:assignment-preview", args=[self.assignment.id])
        )
        self.assertEqual(Submission.objects.filter(assignment=self.assignment).count(), 1)

    @patch(
        "lms_modules.student.views_submit.github_fetch.probe_github_file",
        return_value="not_blob",
    )
    def test_repo_link_is_rejected(self, _probe):
        response = self._submit(["https://github.com/example/repo"])
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "저장소·폴더 링크는 제출할 수 없습니다")
        self.assertFalse(Submission.objects.filter(assignment=self.assignment).exists())

    @patch(
        "lms_modules.student.views_submit.github_fetch.probe_github_file",
        return_value="not_blob",
    )
    def test_folder_tree_link_is_rejected(self, _probe):
        # 2조 develop 기준: repo/tree 링크는 여전히 "not_blob"으로 분류되어 차단된다
        # (AI 채점의 _fetch_folder 는 별개 — 이미 제출된 링크를 나중에 읽을 때만 쓰인다).
        response = self._submit(["https://github.com/example/repo/tree/main/src"])
        self.assertContains(response, "저장소·폴더 링크는 제출할 수 없습니다")
        self.assertFalse(Submission.objects.filter(assignment=self.assignment).exists())

    @patch(
        "lms_modules.student.views_submit.github_fetch.probe_github_file",
        return_value="not_found",
    )
    def test_unreachable_or_private_link_is_rejected_with_message(self, _probe):
        response = self._submit(["https://github.com/example/private/blob/main/x.py"])
        self.assertContains(response, "GitHub 링크를 열 수 없습니다")
        self.assertFalse(Submission.objects.filter(assignment=self.assignment).exists())

    @patch(
        "lms_modules.student.views_submit.github_fetch.probe_github_file",
        return_value="error",
    )
    def test_probe_timeout_or_api_outage_does_not_block_submission(self, _probe):
        # 검증 실패(not_blob/not_found)와 달리, 일시적 오류(error)는 학생을 막지 않는다.
        response = self._submit(["https://github.com/example/repo/blob/main/a.py"])
        self.assertRedirects(
            response, reverse("lms:student:assignment-preview", args=[self.assignment.id])
        )
        self.assertEqual(Submission.objects.filter(assignment=self.assignment).count(), 1)

    def test_non_github_link_is_never_probed(self):
        with patch(
            "lms_modules.student.views_submit.github_fetch.probe_github_file"
        ) as probe:
            self._submit(["https://example.com/portfolio/project"])
        probe.assert_not_called()
        self.assertEqual(Submission.objects.filter(assignment=self.assignment).count(), 1)

    def test_plain_file_submission_still_works(self):
        # 링크 검증 추가가 기존 파일 제출 기능을 회귀시키지 않는지 확인.
        response = self.client.post(
            reverse("lms:student:assignment-submit", args=[self.assignment.id]),
            {"description": "", "files": [SimpleUploadedFile("solution.py", b"print(1)")]},
        )
        self.assertRedirects(
            response, reverse("lms:student:assignment-preview", args=[self.assignment.id])
        )
        submission = Submission.objects.get(assignment=self.assignment)
        self.assertEqual(submission.files.count(), 1)
