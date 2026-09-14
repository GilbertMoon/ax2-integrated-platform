from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from accounts import oauth
from accounts import views as account_views
from apps.ai import views as idea_ai_views
from apps.brainstorm import views as idea_brainstorm_views
from teams import views as team_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls")),
    path("accounts/google/login/", oauth.google_login, name="google_login"),
    path(
        "accounts/google/login/callback/",
        oauth.google_callback,
        name="google_callback",
    ),
    path("accounts/kakao/login/", oauth.kakao_login, name="kakao_login"),
    path(
        "accounts/kakao/login/callback/",
        oauth.kakao_callback,
        name="kakao_callback",
    ),
    path("api/auth/me/", account_views.auth_me_view, name="api_auth_me"),
    path("attendance/", include("attendance.urls")),
    path("teams/", include("teams.urls")),
    path("student/team/", team_views.student_team_page, name="student-team-page"),
    path("reviews/", include("reviews.urls")),
    path("results/", include("results.urls")),
    path("manage/", include("rounds.urls")),
    path("manage/audit/", include("audit.urls")),
    path("manage/notices/", include("notices.urls")),
    path("notifications/", include("notifications.urls")),
    path("lms/", include("lms.urls")),
    path("github/", include("lms_modules.github_sync.urls")),
    path("ideas/", include("apps.common.ideas_urls")),
    path("api/v1/prds/", include("apps.prds.api_urls")),
    path("api/v1/home/", include("apps.prds.home_urls")),
    path("api/v1/prds/<int:prd_id>/ai/", include("apps.ai.api_urls")),
    path(
        "api/v1/prds/<int:prd_id>/brainstorm/",
        include("apps.brainstorm.api_urls"),
    ),
    path(
        "ideas/prds/<int:prd_id>/write/",
        idea_ai_views.prd_write_page,
        name="idea-prd-write",
    ),
    path(
        "ideas/prds/<int:prd_id>/brainstorm/",
        idea_brainstorm_views.brainstorm_page,
        name="idea-brainstorm",
    ),
    path("", account_views.home_view, name="home"),
]

if settings.DEBUG:
    # 개발 서버에서만 업로드된 프로필 사진을 직접 내려준다.
    # 운영에서는 Caddy/whitenoise 등 앞단이 MEDIA_ROOT를 서빙해야 한다.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
