from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase
from django.utils import timezone

from rounds.models import EvaluationRound


class LmsRoundWeightValidationTests(SimpleTestCase):
    def _round(self, **weights):
        start = timezone.now()
        values = {
            "team_score_weight": 40,
            "personal_score_weight": 60,
            "tutor_score_weight": 0,
            "lms_score_weight": 0,
        }
        values.update(weights)
        return EvaluationRound(
            title="LMS weight test",
            evaluation_start_at=start,
            evaluation_end_at=start + timedelta(days=1),
            target_team_count=2,
            **values,
        )

    def test_four_score_weights_can_sum_to_100(self):
        round_obj = self._round(
            team_score_weight=30,
            personal_score_weight=40,
            tutor_score_weight=20,
            lms_score_weight=10,
        )
        round_obj.clean()

    def test_default_weights_keep_existing_40_60_behavior(self):
        round_obj = self._round()
        round_obj.clean()
        self.assertEqual(round_obj.lms_score_weight, 0)

    def test_invalid_four_score_weight_sum_is_rejected(self):
        round_obj = self._round(
            team_score_weight=40,
            personal_score_weight=50,
            tutor_score_weight=0,
            lms_score_weight=20,
        )
        with self.assertRaises(ValidationError):
            round_obj.clean()
