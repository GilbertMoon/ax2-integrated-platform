"""2조 LMS 학생 기능의 통합용 View 진입점.

현재는 기존 4조 백엔드와 충돌하지 않도록 기능을 단계적으로 이식한다.
실제 2조 기능 View는 원본 의존성 검토 후 추가한다.
"""

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from lms_client import services as lms_services


@login_required
def home(request):
    """LMS 영역의 시작점.

    4조 공통 인증을 유지하고 LMS 전용 화면으로 진입한다.
    """
    if request.user.role != "student":
        raise PermissionDenied("학생만 LMS 화면에 접근할 수 있습니다.")
    return redirect("lms:dashboard")


@login_required
def dashboard(request):
    """LMS 대시보드 진입점.

    기존 2조 대시보드의 의존성을 바로 복제하지 않고,
    통합용 구조를 먼저 만든다. LMS 데이터 연동은 이후 단계에서 연결한다.
    """
    if request.user.role != "student":
        raise PermissionDenied("학생만 LMS 화면에 접근할 수 있습니다.")

    return {
        "lms_available": True,
        "student_id": request.user.id,
    }


# 아래 View들은 URL 구조만 먼저 확보한다.
# 실제 구현은 2조 core 모델/템플릿 의존성 검토 후 단계적으로 이식한다.

def _not_ready(request, *args, **kwargs):
    raise PermissionDenied("LMS 통합 기능을 준비 중입니다.")


lecture_list = _not_ready
lecture_detail = _not_ready
assignment_list = _not_ready
assignment_submit = _not_ready
assignment_preview = _not_ready
result_list = _not_ready
resubmit = _not_ready
result = _not_ready
