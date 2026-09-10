from django.db import models
from django.db.models import Q


class Team(models.Model):
    round = models.ForeignKey(
        "rounds.EvaluationRound", on_delete=models.PROTECT, related_name="teams"
    )
    team_number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "팀"
        verbose_name_plural = "팀 목록"
        ordering = ("team_number",)
        constraints = [
            models.UniqueConstraint(fields=("round", "team_number"), name="teams_number_unique"),
            models.CheckConstraint(condition=Q(team_number__gte=1), name="teams_number_positive"),
        ]

    def __str__(self):
        return f"{self.round} / {self.name}"


class TeamMembership(models.Model):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    participant = models.OneToOneField(
        "rounds.RoundParticipant", on_delete=models.PROTECT, related_name="team_membership"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "팀 구성원"
        verbose_name_plural = "팀 구성원 목록"
        ordering = ("team__team_number", "participant__student_number_snapshot")

    def __str__(self):
        return f"{self.team} / {self.participant.display_name_snapshot}"


class TeamFormationSnapshot(models.Model):
    """Immutable evidence for the scores used when saving a team arrangement."""

    round = models.ForeignKey(
        "rounds.EvaluationRound", on_delete=models.PROTECT, related_name="formation_snapshots"
    )
    actor = models.ForeignKey("accounts.User", on_delete=models.PROTECT)
    version = models.PositiveIntegerField()
    evidence = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("round", "version"), name="teams_formation_round_version_unique"
            )
        ]
        ordering = ("-created_at",)

    def __str__(self):
        return f"Round {self.round_id} / version {self.version}"
