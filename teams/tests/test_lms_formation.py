from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from lms_modules.core.models import Assignment, Submission

from accounts.models import User
from results.models import CalculationRun, EvaluationResult
from rounds.models import EvaluationRound, RoundParticipant
from teams.lms_formation import base_scores, calculate, decode, selection
from teams.models import Team, TeamFormationSnapshot, TeamMembership


class LmsFormationTests(TestCase):
    databases = {"default", "assignment_lms"}

    def setUp(self):
        self.now = timezone.now()
        self.tutor = User.objects.create_user(
            email="formation-tutor@example.com",
            role=User.Role.TUTOR,
            approval_status=User.ApprovalStatus.APPROVED,
            must_rotate_password=False,
        )
        self.round = EvaluationRound.objects.create(
            title="Next",
            created_by=self.tutor,
            evaluation_start_at=self.now,
            evaluation_end_at=self.now + timedelta(days=1),
            target_team_count=2,
        )
        self.people = []
        for i in range(4):
            user = User.objects.create_user(
                email=f"formation-{i}@example.com",
                role=User.Role.STUDENT,
                approval_status=User.ApprovalStatus.APPROVED,
                must_rotate_password=False,
            )
            self.people.append(
                RoundParticipant.objects.create(
                    round=self.round,
                    user=user,
                    student_number_snapshot=str(i),
                    display_name_snapshot=str(i),
                )
            )
        self.assignment = Assignment.objects.create(
            title="Task", created_by=self.tutor.pk, due_at=self.now - timedelta(days=1)
        )
        for p in self.people:
            Submission.objects.create(
                assignment=self.assignment, student_id=p.user_id, final_score=80
            )

    def chosen(self, weight=100, rid=None):
        return {
            "enabled": True,
            "weight": weight,
            "items": [{"assignment_id": self.assignment.pk, "round_id": rid}],
        }

    def post(self, name, payload):
        self.login(self.tutor)
        return self.client.post(
            reverse("teams:" + name, args=[self.round.pk]), payload, content_type="application/json"
        )

    def login(self, user):
        self.client.force_login(user)
        session = self.client.session
        session["auth_session_version"] = user.auth_session_version
        session.save()

    def test_latest_grade_is_used_without_modifying_submissions(self):
        scores, evidence = calculate(self.round.pk, self.chosen())
        self.assertEqual(set(scores.values()), {Decimal("4.3")})
        self.assertEqual(evidence["students"][str(self.people[0].pk)]["lms_total"], 86)
        Submission.objects.filter(student_id=self.people[0].user_id).update(final_score=100)
        scores, _ = calculate(self.round.pk, self.chosen())
        self.assertEqual(scores[self.people[0].pk], Decimal("5"))
        self.assertEqual(Submission.objects.count(), 4)

    def test_weighted_score_and_missing_base(self):
        bases = {p.pk: Decimal("4") for p in self.people}
        bases[self.people[-1].pk] = None
        with patch("teams.lms_formation.base_scores", return_value=(bases, {})):
            scores, _ = calculate(self.round.pk, self.chosen(30))
        self.assertEqual(scores[self.people[0].pk], Decimal("4.09"))
        self.assertIsNone(scores[self.people[-1].pk])

    def test_disabled_does_not_query_lms(self):
        with self.assertNumQueries(0, using="assignment_lms"):
            scores, _ = calculate(self.round.pk, {"enabled": False})
        self.assertEqual(set(scores.values()), {None})

    def test_existing_lms_contribution_is_removed_and_result_unchanged(self):
        old = EvaluationRound.objects.create(
            title="Scored",
            created_by=self.tutor,
            evaluation_start_at=self.now - timedelta(days=3),
            evaluation_end_at=self.now - timedelta(days=2),
            status="COMPLETED",
            completed_at=self.now - timedelta(days=1),
            team_score_weight=40,
            personal_score_weight=40,
            tutor_score_weight=0,
            lms_score_weight=20,
        )
        p = RoundParticipant.objects.create(
            round=old,
            user=self.people[0].user,
            student_number_snapshot="old",
            display_name_snapshot="old",
        )
        run = CalculationRun.objects.create(
            round=old,
            version=1,
            status="SUCCEEDED",
            is_active=True,
            formula_version="v1",
            executed_by=self.tutor,
        )
        row = EvaluationResult.objects.create(
            calculation_run=run,
            result_type="INDIVIDUAL",
            participant=p,
            team_score_raw=3,
            peer_score_raw=4,
            lms_score_raw=5,
            final_score_raw=Decimal("3.8"),
        )
        scores, _ = base_scores({self.people[0].pk: p.user_id}, self.round.pk)
        self.assertEqual(scores[self.people[0].pk], Decimal("3.5"))
        row.refresh_from_db()
        self.assertEqual(row.final_score_raw, Decimal("3.8"))
        old.team_score_weight = 30
        old.personal_score_weight = 40
        old.lms_score_weight = 30
        old.save()
        with self.assertRaisesMessage(ValidationError, "일치하지 않습니다"):
            base_scores({self.people[0].pk: p.user_id}, self.round.pk)

    def test_snapshot_failure_rolls_back_team_save(self):
        response = self.post(
            "auto-assignment", {"team_count": 2, "lock_version": 0, "lms_selection": self.chosen()}
        )
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        with patch(
            "teams.models.TeamFormationSnapshot.objects.create",
            side_effect=RuntimeError("snapshot failed"),
        ):
            with patch("teams.views._notify_team_assignments") as notify:
                with self.assertRaisesMessage(RuntimeError, "snapshot failed"):
                    self.post(
                        "save-team",
                        {
                            "lock_version": 0,
                            "teams": body["teams"],
                            "formation_token": body["formation_token"],
                            "formation_required": True,
                        },
                    )
                notify.assert_not_called()
        self.round.refresh_from_db()
        self.assertEqual(self.round.lock_version, 0)
        self.assertFalse(Team.objects.filter(round=self.round).exists())

    def test_ungraded_and_future_tasks_are_rejected(self):
        Submission.objects.filter(student_id=self.people[0].user_id).update(final_score=None)
        with self.assertRaisesMessage(ValidationError, "미채점"):
            calculate(self.round.pk, self.chosen())
        self.assignment.due_at = self.now + timedelta(days=1)
        self.assignment.save()
        with self.assertRaisesMessage(ValidationError, "마감 전"):
            calculate(self.round.pk, self.chosen())

    def test_historical_team_submission_and_missing_membership(self):
        old = EvaluationRound.objects.create(
            title="Old",
            created_by=self.tutor,
            evaluation_start_at=self.now - timedelta(days=3),
            evaluation_end_at=self.now - timedelta(hours=1),
        )
        participant = RoundParticipant.objects.create(
            round=old,
            user=self.people[0].user,
            student_number_snapshot="old",
            display_name_snapshot="old",
        )
        team = Team.objects.create(round=old, team_number=1, name="Old team")
        TeamMembership.objects.create(team=team, participant=participant)
        self.assignment.is_team = True
        self.assignment.save()
        Submission.objects.create(assignment=self.assignment, team_id=team.pk, final_score=100)
        scores, _ = calculate(self.round.pk, self.chosen(rid=old.pk))
        self.assertEqual(scores[self.people[0].pk], Decimal("5"))
        self.assertIsNone(scores[self.people[1].pk])
        with self.assertRaisesMessage(ValidationError, "회차"):
            calculate(self.round.pk, self.chosen())

    def test_selection_has_no_fixed_count_limit_and_deduplicates(self):
        raw = self.chosen()
        raw["items"] = [{"assignment_id": i, "round_id": None} for i in range(1, 501)] * 2
        self.assertEqual(len(selection(raw)["items"]), 500)
        raw["items"].append({"assignment_id": 1, "round_id": 2})
        with self.assertRaises(ValidationError):
            selection(raw)

    def test_manual_board_save_keeps_signed_evidence_and_rejects_stale_token(self):
        response = self.post(
            "auto-assignment",
            {
                "team_count": 2,
                "lock_version": 0,
                "lms_selection": self.chosen(),
                "scores_only": True,
            },
        )
        self.assertEqual(response.status_code, 200, response.content)
        body = response.json()
        self.assertNotIn("teams", body)
        token = body["formation_token"]
        with self.assertRaises(ValidationError):
            decode(token + "tampered", self.round.pk, 0, self.tutor.pk)
        with self.assertRaises(ValidationError):
            decode(token, self.round.pk, 0, self.people[0].user_id)
        payload = {
            "lock_version": 0,
            "formation_required": True,
            "formation_token": token,
            "teams": [
                {
                    "team_number": i + 1,
                    "name": f"Team {i + 1}",
                    "participant_ids": [p.pk for p in self.people[i * 2 : i * 2 + 2]],
                }
                for i in range(2)
            ],
        }
        with patch("teams.views._notify_team_assignments"):
            saved = self.post("save-team", payload)
        self.assertEqual(saved.status_code, 200, saved.content)
        snapshot = TeamFormationSnapshot.objects.get(round=self.round)
        self.assertEqual(snapshot.version, 1)
        self.assertEqual(snapshot.evidence["selection"]["weight"], 100)
        self.assertEqual(TeamMembership.objects.count(), 4)
        page = self.client.get(reverse("teams:management-page", args=[self.round.pk]))
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.context["team_data"]["seed_scores"], snapshot.evidence["seed_scores"])
        self.assertEqual(
            page.context["team_data"]["formation_evidence"]["selection"],
            snapshot.evidence["selection"],
        )
        payload["lock_version"] = 1
        with patch("teams.views._notify_team_assignments") as notify:
            self.assertEqual(self.post("save-team", payload).status_code, 400)
            notify.assert_not_called()

    def test_catalog_invalid_round_and_student_permission(self):
        url = reverse("teams:lms-catalog", args=[self.round.pk])
        self.login(self.tutor)
        self.assertEqual(self.client.get(url, {"source_round": 999999}).status_code, 400)
        self.login(self.people[0].user)
        self.assertEqual(self.client.get(url).status_code, 403)
