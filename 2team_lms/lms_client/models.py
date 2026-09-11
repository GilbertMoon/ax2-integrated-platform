from django.db import models


class RoundScore(models.Model):
    """2조 LMS의 회차별 학생 점수 스냅샷을 읽기 위한 unmanaged 모델."""

    round_id = models.BigIntegerField()
    round_title = models.CharField(max_length=200, blank=True)
    student_id = models.IntegerField()
    student_name = models.CharField(max_length=150, blank=True)
    total = models.FloatField(null=True, blank=True)
    achievement = models.FloatField(null=True, blank=True)
    sincerity = models.FloatField(null=True, blank=True)
    team_included = models.BooleanField(default=False)
    graded_count = models.PositiveSmallIntegerField(default=0)
    ungraded_count = models.PositiveSmallIntegerField(default=0)
    total_count = models.PositiveSmallIntegerField(default=0)
    breakdown = models.JSONField(default=dict, blank=True)
    assignment_ids = models.JSONField(default=list, blank=True)
    policy_snapshot = models.JSONField(default=dict, blank=True)
    closed_at = models.DateTimeField()
    closed_by = models.IntegerField()

    class Meta:
        managed = False
        db_table = "round_score"
        unique_together = (("round_id", "student_id"),)

    def __str__(self):
        return f"round {self.round_id} · student {self.student_id} · {self.total}"
