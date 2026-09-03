from django.test import SimpleTestCase
from django.urls import reverse


class ProjectRoundUrlTests(SimpleTestCase):
    def test_project_round_is_manage_rounds(self):
        self.assertEqual(reverse("rounds:project-list"), "/manage/rounds/")

    def test_project_round_detail_is_under_manage_rounds(self):
        self.assertEqual(reverse("rounds:project-detail", kwargs={"round_id": 10}), "/manage/rounds/10/")

    def test_evaluation_round_list_is_separate(self):
        self.assertEqual(reverse("rounds:list"), "/manage/evaluation-rounds/")

    def test_evaluation_round_create_is_separate(self):
        self.assertEqual(reverse("rounds:create"), "/manage/evaluation-rounds/new/")

    def test_evaluation_round_edit_is_separate(self):
        self.assertEqual(reverse("rounds:edit", kwargs={"round_id": 10}), "/manage/evaluation-rounds/10/")
