"""2조 LMS 화면에서 사용할 외부 학생 ID."""

from django.conf import settings


DEV_STUDENT_ID = 11


def external_student_id(request) -> int:
    """개발 로그인 우회 중에는 가상 학생 ID, 실제 로그인에서는 로그인 사용자 ID."""
    if getattr(settings, "DEV_SKIP_AUTH", False):
        return DEV_STUDENT_ID
    return request.user.id
