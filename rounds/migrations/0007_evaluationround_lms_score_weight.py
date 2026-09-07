# Generated manually for LMS score weight integration.

import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rounds", "0006_alter_evaluationround_options_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="evaluationround",
            name="rounds_score_weight_range",
        ),
        migrations.RemoveConstraint(
            model_name="evaluationround",
            name="rounds_score_weight_sums_to_100",
        ),
        migrations.AddField(
            model_name="evaluationround",
            name="lms_score_weight",
            field=models.PositiveSmallIntegerField(default=0),
        ),
        migrations.AddConstraint(
            model_name="evaluationround",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    ("team_score_weight__gte", 0),
                    ("team_score_weight__lte", 100),
                    ("personal_score_weight__gte", 0),
                    ("personal_score_weight__lte", 100),
                    ("tutor_score_weight__gte", 0),
                    ("tutor_score_weight__lte", 100),
                    ("lms_score_weight__gte", 0),
                    ("lms_score_weight__lte", 100),
                ),
                name="rounds_score_weight_range",
            ),
        ),
        migrations.AddConstraint(
            model_name="evaluationround",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    (
                        "team_score_weight",
                        django.db.models.expressions.CombinedExpression(
                            django.db.models.expressions.CombinedExpression(
                                django.db.models.expressions.CombinedExpression(
                                    models.Value(100), "-", models.F("personal_score_weight")
                                ),
                                "-",
                                models.F("tutor_score_weight"),
                            ),
                            "-",
                            models.F("lms_score_weight"),
                        ),
                    )
                ),
                name="rounds_score_weight_sums_to_100",
            ),
        ),
    ]
