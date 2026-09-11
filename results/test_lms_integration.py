from decimal import Decimal

from django.test import SimpleTestCase
from lms_client.services import normalize_score

from results.services import calculate_final_score


class LmsScoreIntegrationTests(SimpleTestCase):
    def test_lms_score_is_normalized_to_five_point_scale(self):
        self.assertEqual(normalize_score(87), 4.35)
        self.assertEqual(normalize_score(7), 0.35)
        self.assertEqual(normalize_score(0), 0.0)
        self.assertEqual(normalize_score(100), 5.0)

    def test_existing_default_formula_is_unchanged_when_lms_weight_is_zero(self):
        score = calculate_final_score(Decimal("4"), Decimal("5"))
        self.assertEqual(score, Decimal("4.600000"))

    def test_lms_score_is_included_with_round_weight(self):
        score = calculate_final_score(
            Decimal("4"),
            Decimal("5"),
            None,
            Decimal("4.35"),
            team_weight=Decimal("0.30"),
            peer_weight=Decimal("0.60"),
            tutor_weight=Decimal("0"),
            lms_weight=Decimal("0.10"),
        )
        self.assertEqual(score, Decimal("4.635000"))

    def test_missing_lms_snapshot_makes_final_score_na_when_lms_is_required(self):
        score = calculate_final_score(
            Decimal("4"),
            Decimal("5"),
            None,
            None,
            team_weight=Decimal("0.30"),
            peer_weight=Decimal("0.60"),
            tutor_weight=Decimal("0"),
            lms_weight=Decimal("0.10"),
        )
        self.assertIsNone(score)

    def test_zero_lms_score_is_a_real_score_not_na(self):
        score = calculate_final_score(
            Decimal("1"),
            Decimal("1"),
            None,
            Decimal("0"),
            team_weight=Decimal("0"),
            peer_weight=Decimal("0"),
            tutor_weight=Decimal("0"),
            lms_weight=Decimal("1"),
        )
        self.assertEqual(score, Decimal("0.000000"))
