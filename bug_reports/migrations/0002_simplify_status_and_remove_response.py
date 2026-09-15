from django.db import migrations, models


def normalize_status(apps, schema_editor):
    BugReport = apps.get_model("bug_reports", "BugReport")
    BugReport.objects.filter(status="in_progress").update(status="open")


class Migration(migrations.Migration):
    dependencies = [("bug_reports", "0001_initial")]

    operations = [
        migrations.RunPython(normalize_status, migrations.RunPython.noop),
        migrations.RemoveField(model_name="bugreport", name="response"),
        migrations.AlterField(
            model_name="bugreport",
            name="status",
            field=models.CharField(
                choices=[("open", "접수 완료"), ("resolved", "해결 완료")],
                default="open",
                max_length=20,
                verbose_name="처리 상태",
            ),
        ),
    ]
