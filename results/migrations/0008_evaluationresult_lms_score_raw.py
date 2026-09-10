# Generated manually for LMS score integration.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("results", "0007_alter_calculationrun_options_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="evaluationresult",
            name="results_final_score_five_point_range",
        ),
        migrations.RemoveConstraint(
            model_name="evaluationresult",
            name="results_display_score_five_point_range",
        ),
        migrations.AddField(
            model_name="evaluationresult",
            name="lms_score_raw",
            field=models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True),
        ),
        migrations.AddConstraint(
            model_name="evaluationresult",
            constraint=models.CheckConstraint(
                condition=models.Q(("lms_score_raw__isnull", True))
                | models.Q(("lms_score_raw__gte", 0), ("lms_score_raw__lte", 5)),
                name="results_lms_score_five_point_range",
            ),
        ),
        migrations.AddConstraint(
            model_name="evaluationresult",
            constraint=models.CheckConstraint(
                condition=models.Q(("final_score_raw__isnull", True))
                | models.Q(("final_score_raw__gte", 0), ("final_score_raw__lte", 5)),
                name="results_final_score_five_point_range",
            ),
        ),
        migrations.AddConstraint(
            model_name="evaluationresult",
            constraint=models.CheckConstraint(
                condition=models.Q(("display_score__isnull", True))
                | models.Q(("display_score__gte", 0), ("display_score__lte", 5)),
                name="results_display_score_five_point_range",
            ),
        ),
    ]
