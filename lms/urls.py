from django.urls import path

from . import views

app_name = "lms"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("lecture/", views.lecture_list, name="lecture-list"),
    path("lecture/<int:lesson_id>/", views.lecture_detail, name="lecture-detail"),
    path("assignments/", views.assignment_list, name="assignment-list"),
    path("assignments/<int:assignment_id>/submit/", views.assignment_submit, name="assignment-submit"),
    path("assignments/<int:assignment_id>/preview/", views.assignment_preview, name="assignment-preview"),
    path("results/", views.result_list, name="result-list"),
    path("submissions/<int:submission_id>/resubmit/", views.resubmit, name="submission-resubmit"),
    path("submissions/<int:submission_id>/result/", views.result, name="submission-result"),
]
