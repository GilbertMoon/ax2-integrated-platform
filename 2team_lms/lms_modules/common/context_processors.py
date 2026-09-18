"""
apps/common/context_processors.py — 공통 담당 전담

모든 템플릿에 현재 사용자 역할과 URL 네임스페이스를 넣어준다.
sidebar.html 등 공통 shell 이 role 로 메뉴를 분기하는 데 사용.
"""
from django.conf import settings

from lms_modules.accounts_client import services as accounts


def nav(request):
    match = getattr(request, "resolver_match", None)
    if not match or "lms" not in match.namespaces:
        return {}
    role = None
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        if getattr(settings, "DEV_SKIP_AUTH", False):
            # 개발 모드: 역할 게이트는 열려 있고(services.is_tutor/is_student 항상 True),
            # 사이드바 메뉴만 DEV_ROLE 로 정한다.
            role = getattr(settings, "DEV_ROLE", "TUTOR")
        elif accounts.is_tutor(user.id):
            role = "TUTOR"
        elif accounts.is_student(user.id):
            role = "STUDENT"

    match = getattr(request, "resolver_match", None)
    
    if getattr(settings, "DEV_SKIP_AUTH", False):
        # 튜터 URL은 "/tutor/"가 아니라 바깥쪽 "/lms/" 프리픽스 아래
        # "/lms/tutor/"로 물려 있다 (2team_lms/lms/urls.py) — startswith("/tutor/")는
        # 여기서 절대 참이 될 수 없어 항상 STUDENT로 떨어지던 버그.
        if "/tutor/" in request.path:
            role = "TUTOR"
        else:
            role = "STUDENT"

    return {
        "nav_role": role,
        "url_namespace": match.namespaces[-1] if match else "",
        "url_name": match.url_name if match else "",
    }


def analytics(request):
    return {"ga_measurement_id": getattr(settings, "GA_MEASUREMENT_ID", "")}
