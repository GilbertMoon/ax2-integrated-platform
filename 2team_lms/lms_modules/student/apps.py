from django.apps import AppConfig


class StudentConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "lms_modules.student"
    label = "student"
    verbose_name = "학생"
