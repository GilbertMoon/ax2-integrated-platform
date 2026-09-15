from django.urls import path

from bug_reports import views

app_name = "bug_reports"
urlpatterns = [
    path("", views.index, name="index"),
    path("new/", views.create, name="create"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/screenshot/", views.screenshot, name="screenshot"),
]
