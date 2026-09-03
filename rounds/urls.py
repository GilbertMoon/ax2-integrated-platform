from django.urls import path

from results import views as result_views
from rounds import project_views, views
from teams import views as team_views

app_name = "rounds"

urlpatterns = [
    path("", views.operations_dashboard, name="dashboard"),
    path("templates/", views.template_list, name="template-list"),
    path("templates/new/", views.template_edit, name="template-create"),
    path("templates/<int:template_id>/", views.template_edit, name="template-edit"),
    path("templates/<int:template_id>/copy/", views.template_copy, name="template-copy"),
    path("templates/<int:template_id>/delete/", views.template_delete, name="template-delete"),
    path("templates/<int:template_id>/archive/", views.template_archive, name="template-archive"),
    path("templates/<int:template_id>/restore/", views.template_restore, name="template-restore"),

    # Project-round management: /manage/rounds/
    path("rounds/", project_views.project_list, name="project-list"),
    path("rounds/<int:round_id>/", project_views.project_detail, name="project-detail"),
    path("rounds/<int:round_id>/teams/", team_views.management_team_page, name="teams"),

    # Evaluation-round management: /manage/evaluation-rounds/
    path("evaluation-rounds/", views.round_list, name="list"),
    path("evaluation-rounds/new/", views.round_edit, name="create"),
    path("evaluation-rounds/<int:round_id>/", views.round_edit, name="edit"),
    path("evaluation-rounds/<int:round_id>/start/", views.round_start, name="start"),
    path("evaluation-rounds/<int:round_id>/reviews/", views.round_reviews, name="reviews"),
    path(
        "evaluation-rounds/<int:round_id>/tutor-evaluation/",
        views.tutor_evaluation,
        name="tutor-evaluation",
    ),
    path(
        "evaluation-rounds/<int:round_id>/tutor-review/",
        views.tutor_review_list,
        name="tutor-review-list",
    ),
    path(
        "evaluation-rounds/<int:round_id>/tutor-review/<int:participant_id>/",
        views.tutor_review_form,
        name="tutor-review-form",
    ),
    path(
        "evaluation-rounds/<int:round_id>/tutor-team-review/",
        views.tutor_team_review_list,
        name="tutor-team-review-list",
    ),
    path(
        "evaluation-rounds/<int:round_id>/tutor-team-review/<int:team_id>/",
        views.tutor_team_review_form,
        name="tutor-team-review-form",
    ),
    path("evaluation-rounds/<int:round_id>/complete/", views.round_complete, name="complete"),
    path(
        "evaluation-rounds/<int:round_id>/send-reminders/",
        views.send_submission_reminders_view,
        name="send_reminders",
    ),
    path("evaluation-rounds/<int:round_id>/delete/", views.round_delete, name="delete"),
    path("evaluation-rounds/<int:round_id>/revert/", views.round_revert, name="revert"),
    path("evaluation-rounds/<int:round_id>/reopen/", views.round_reopen, name="reopen"),
    path("evaluation-rounds/<int:round_id>/results/", result_views.manage_results, name="results"),
    path(
        "evaluation-rounds/<int:round_id>/results/publish-settings/",
        result_views.publish_settings,
        name="publish-settings",
    ),
    path(
        "evaluation-rounds/<int:round_id>/results/calculate/",
        result_views.calculate,
        name="calculate-results",
    ),
    path(
        "evaluation-rounds/<int:round_id>/results/publish/<str:item_key>/",
        result_views.publish,
        name="publish-results",
    ),
    path(
        "evaluation-rounds/<int:round_id>/results/publish-all/",
        result_views.publish_all,
        name="publish-all-results",
    ),

    path("results/", views.results_entry, name="results-entry"),
    path("publish/", views.publish_entry, name="publish-entry"),
    path("tutor-evaluation/", views.tutor_evaluation_entry, name="tutor-evaluation-entry"),
]
