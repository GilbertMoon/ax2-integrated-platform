"""강의 자료(LessonMaterial) 실제 업로드/다운로드 회귀 테스트.

이전에는 튜터가 파일을 골라도 서버에 업로드되지 않고(파일명 문자열만 저장),
학생 다운로드 버튼은 실제 파일과 무관한 목업(mock) txt 를 내려줬다. 이 테스트는
그 버그가 다시 생기지 않는지를 확인한다:
  - 업로드 API 가 실제로 스토리지에 파일을 저장하고 (url, file_name, file_size) 를 돌려주는지
  - lessons 저장 API 가 그 file_name/file_size 를 LessonMaterial 에 반영하는지
  - 다운로드 뷰가 저장된 실제 바이트를 원래 파일명으로 돌려주는지
"""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from lms_modules.core.models import Lecture, Lesson, LessonMaterial


@override_settings(DEV_SKIP_AUTH=True)
class LectureMaterialUploadTests(TestCase):
    databases = {"default", "assignment_lms"}

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            approval_status="approved",
            is_active=True,
            is_onboarded=True,
            email="tutor-lecture@example.com",
            password="pw",
        )
        self.client.force_login(self.user)
        p = patch("lms_modules.tutor.views_manage.accounts.is_tutor", return_value=True)
        p.start()
        self.addCleanup(p.stop)

    def test_upload_persists_real_bytes_and_returns_metadata(self):
        upload = SimpleUploadedFile(
            "syllabus.pdf", b"%PDF-1.4 fake pdf bytes", content_type="application/pdf"
        )
        resp = self.client.post(
            reverse("lms:tutor:lecture-material-upload"), {"file": upload}
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["file_name"], "syllabus.pdf")
        self.assertEqual(data["file_size"], len(b"%PDF-1.4 fake pdf bytes"))
        self.assertTrue(data["url"])

    def test_upload_rejects_oversized_file(self):
        with patch("lms_modules.tutor.views_lecture.MAX_MATERIAL_SIZE", 10):
            upload = SimpleUploadedFile("big.bin", b"x" * 20)
            resp = self.client.post(
                reverse("lms:tutor:lecture-material-upload"), {"file": upload}
            )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["status"], "error")

    def test_upload_requires_a_file(self):
        resp = self.client.post(reverse("lms:tutor:lecture-material-upload"), {})
        self.assertEqual(resp.status_code, 400)

    def test_anonymous_cannot_upload(self):
        self.client.logout()
        upload = SimpleUploadedFile("x.txt", b"hi")
        resp = self.client.post(
            reverse("lms:tutor:lecture-material-upload"), {"file": upload}
        )
        self.assertNotEqual(resp.status_code, 200)


@override_settings(DEV_SKIP_AUTH=True)
class LectureUpdateApiMaterialTests(TestCase):
    databases = {"default", "assignment_lms"}

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            approval_status="approved",
            is_active=True,
            is_onboarded=True,
            email="tutor-lecture2@example.com",
            password="pw",
        )
        self.client.force_login(self.user)
        p = patch("lms_modules.tutor.views_manage.accounts.is_tutor", return_value=True)
        p.start()
        self.addCleanup(p.stop)

    def test_saving_lessons_stores_file_name_and_size(self):
        payload = {
            "lessons": [
                {
                    "id": None,
                    "title": "1주차",
                    "date": "2026-09-01",
                    "videos": [],
                    "materials": [
                        {
                            "kind": "FILE",
                            "title": "교안",
                            "url": "/lms-media/lesson_materials/abc_syllabus.pdf",
                            "file_name": "syllabus.pdf",
                            "file_size": 1234,
                        }
                    ],
                }
            ],
            "base_revision": None,
        }
        resp = self.client.post(
            reverse("lms:tutor:lecture-update-api"),
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "success")

        material = LessonMaterial.objects.get(title="교안")
        self.assertEqual(material.file_name, "syllabus.pdf")
        self.assertEqual(material.file_size, 1234)
        self.assertEqual(material.file_url, "/lms-media/lesson_materials/abc_syllabus.pdf")

        # _serialize_lessons 로 되읽었을 때도 file_name 이 그대로 나와야
        # (수정 화면에서 파일을 다시 안 고른 기존 자료가) 다음 저장에서 안 없어진다.
        resp2 = self.client.get(reverse("lms:tutor:lecture"))
        served_materials = resp2.context["lessons"][0]["materials"]
        self.assertEqual(served_materials[0]["file_name"], "syllabus.pdf")


@override_settings(DEV_SKIP_AUTH=True)
class LectureMaterialDownloadTests(TestCase):
    databases = {"default", "assignment_lms"}

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            approval_status="approved",
            is_active=True,
            is_onboarded=True,
            email="student-lecture@example.com",
            password="pw",
        )
        self.client.force_login(self.user)
        p = patch("lms_modules.core.views.accounts.is_student", return_value=True)
        p.start()
        self.addCleanup(p.stop)
        p2 = patch("lms_modules.core.views.accounts.is_tutor", return_value=False)
        p2.start()
        self.addCleanup(p2.stop)

        lecture = Lecture.get_singleton()
        self.lesson = Lesson.objects.create(
            lecture=lecture, title="1주차", lesson_date="2026-09-01"
        )

    def _material_with_real_file(self, content=b"real pdf bytes"):
        from django.core.files.base import ContentFile

        from lms_modules.storage import default_storage

        stored = default_storage.save(
            "lesson_materials/tests_syllabus.pdf", ContentFile(content)
        )
        return LessonMaterial.objects.create(
            lesson=self.lesson,
            kind=LessonMaterial.Kind.FILE,
            title="교안",
            file_url=default_storage.url(stored),
            file_name="syllabus.pdf",
            file_size=len(content),
        )

    def test_download_returns_real_uploaded_bytes(self):
        material = self._material_with_real_file(b"this is the real tutor file")
        resp = self.client.get(
            reverse("lms:core:lecture-material-download", args=[material.pk])
        )
        self.assertEqual(resp.status_code, 200)
        content = b"".join(resp.streaming_content)
        self.assertEqual(content, b"this is the real tutor file")
        self.assertIn("syllabus.pdf", resp["Content-Disposition"])

    def test_download_404s_when_file_missing_from_storage(self):
        material = LessonMaterial.objects.create(
            lesson=self.lesson,
            kind=LessonMaterial.Kind.FILE,
            title="깨진 자료",
            file_url="/lms-media/lesson_materials/does-not-exist.pdf",
            file_name="does-not-exist.pdf",
            file_size=0,
        )
        resp = self.client.get(
            reverse("lms:core:lecture-material-download", args=[material.pk])
        )
        self.assertEqual(resp.status_code, 404)

    def test_link_kind_material_has_no_download_route_match(self):
        material = LessonMaterial.objects.create(
            lesson=self.lesson,
            kind=LessonMaterial.Kind.LINK,
            title="링크 자료",
            link_url="https://example.com",
        )
        resp = self.client.get(
            reverse("lms:core:lecture-material-download", args=[material.pk])
        )
        self.assertEqual(resp.status_code, 404)
