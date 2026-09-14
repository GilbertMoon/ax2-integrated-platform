from django.contrib.auth.decorators import login_required
from django.urls import include, path
from lms_modules.student.views_lecture import (
    student_lecture_detail_view, student_lecture_list_view,
)

app_name = "lms"
urlpatterns = [
    # Keep the previously published lecture names and paths.
    path("lecture/", login_required(student_lecture_list_view), name="lecture-list"),
    path("lecture/<int:lesson_id>/", login_required(student_lecture_detail_view), name="lecture-detail"),
    path("github/", include("lms_modules.github_sync.urls")),
    path("tutor/", include("lms_modules.tutor.urls")),
    path("", include("lms_modules.core.urls")),
    path("", include("lms_modules.student.urls")),
]
