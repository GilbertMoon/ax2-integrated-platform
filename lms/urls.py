from django.urls import path

from .student.views_lecture import (
    student_lecture_detail_view,
    student_lecture_list_view,
)

app_name = "lms"

urlpatterns = [
    path("lecture/", student_lecture_list_view, name="lecture-list"),
    path(
        "lecture/<int:lesson_id>/",
        student_lecture_detail_view,
        name="lecture-detail",
    ),
]
