from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path(
        "assignments/files/<int:file_id>/download/",
        views.assignment_file_download,
        name="assignment-file-download",
    ),
    path(
        "lecture-materials/<int:material_id>/download/",
        views.lecture_material_download,
        name="lecture-material-download",
    ),
]
