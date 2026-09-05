from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import AssessmentRecord
from accounts.views import _safe_int, _safe_float


class ReportPageTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_safe_helpers(self):
        self.assertEqual(_safe_int("42"), 42)
        self.assertEqual(_safe_int("", 10), 10)
        self.assertEqual(_safe_int(None, 5), 5)
        self.assertEqual(_safe_int("invalid", 7), 7)
        self.assertEqual(_safe_float("3.14"), 3.14)
        self.assertEqual(_safe_float("", 5.5), 5.5)
        self.assertEqual(_safe_float(None, 2.0), 2.0)
        self.assertEqual(_safe_float("bad", 1.0), 1.0)

    def test_report_page_with_empty_session(self):
        """Report should render with defaults and not crash with 500 error."""
        response = self.client.get(reverse("report"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cognitive Assessment Report")
        self.assertContains(response, "report-chart-data")
        self.assertContains(response, "Participant")

    def test_report_page_with_populated_session(self):
        """Report should calculate and persist assessment scores accurately."""
        session = self.client.session
        session["name"] = "Alice Smith"
        session["age"] = 32
        session["gender"] = "Female"
        session["sleep_duration"] = 8.0
        session["stress_level"] = 3
        session["screen_time"] = "4-6"
        session["exercise_frequency"] = "High"
        session["reaction_time"] = 230.0
        session["visual_memory_score"] = 28
        session["recognition_score"] = 24
        session["object_location_score"] = 22
        session["delayed_recall_score"] = 18
        session["clock_score"] = 19
        session["clock_contour_score"] = 4
        session["clock_numbers_score"] = 8
        session["clock_hands_score"] = 7
        session.save()

        response = self.client.get(reverse("report"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Alice Smith")
        self.assertContains(response, "report-chart-data")

        # Verify record in database
        record = AssessmentRecord.objects.filter(name="Alice Smith").first()
        self.assertIsNotNone(record)
        self.assertEqual(record.memory_score, 28 + 24 + 22 + 18)
        self.assertEqual(record.clock_score, 19)
        self.assertGreater(record.cognitive_score, 0)

    def test_retake_assessment_clears_session(self):
        """Retake route should clear assessment keys and redirect to instructions."""
        session = self.client.session
        session["name"] = "Bob"
        session["assessment_record_id"] = 999
        session["reaction_time"] = 400.0
        session.save()

        response = self.client.get(reverse("retake_assessment"))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("instructions"))

        # Verify keys were cleared
        refreshed_session = self.client.session
        self.assertNotIn("assessment_record_id", refreshed_session)
        self.assertNotIn("reaction_time", refreshed_session)

    def test_session_debug_html_rendering(self):
        """Debug page should render HTML dashboard with all marks and details."""
        session = self.client.session
        session["name"] = "Carol Danvers"
        session["age"] = 30
        session["gender"] = "Female"
        session["reaction_time"] = 250.0
        session["visual_memory_score"] = 25
        session["recognition_score"] = 20
        session["object_location_score"] = 20
        session["delayed_recall_score"] = 15
        session.save()

        response = self.client.get(reverse("session_debug"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Session Debug & Marks Inspection")
        self.assertContains(response, "Carol Danvers")
        self.assertContains(response, "250")

    def test_session_debug_json_format(self):
        """Debug endpoint should return JSON when format=json parameter is passed."""
        session = self.client.session
        session["name"] = "David Banner"
        session["reaction_time"] = 280.0
        session.save()

        response = self.client.get(reverse("session_debug") + "?format=json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("name"), "David Banner")
        self.assertEqual(response.json().get("reaction_time"), 280.0)

    def test_dynamic_memory_games(self):
        """Recognition, Object Location, and Delayed Recall views should dynamically generate random game data."""
        # Recognition
        res_rec = self.client.get(reverse("recognition_memory"))
        self.assertEqual(res_rec.status_code, 200)
        self.assertIn("recognition_study_icons", self.client.session)
        self.assertEqual(len(self.client.session["recognition_study_icons"]), 8)

        # Object Location
        res_loc = self.client.get(reverse("object_location_memory"))
        self.assertEqual(res_loc.status_code, 200)
        self.assertIn("object_location_game_data", self.client.session)
        self.assertEqual(len(self.client.session["object_location_game_data"]), 3)

        # Delayed Recall
        res_del = self.client.get(reverse("delayed_recall"))
        self.assertEqual(res_del.status_code, 200)
        self.assertIn("delayed_recall_questions", self.client.session)
        self.assertEqual(len(self.client.session["delayed_recall_questions"]), 4)

    def test_save_delayed_recall_returns_all_scores(self):
        """save_delayed_recall endpoint must return total_memory_score and breakdown scores."""
        session = self.client.session
        session["visual_memory_score"] = 24
        session["recognition_score"] = 20
        session["object_location_score"] = 20
        session.save()

        response = self.client.post(
            reverse("save_delayed_recall"),
            data={"delayed_recall_score": 15},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("visual_memory_score"), 24)
        self.assertEqual(data.get("recognition_score"), 20)
        self.assertEqual(data.get("object_location_score"), 20)
        self.assertEqual(data.get("delayed_recall_score"), 15)
        self.assertEqual(data.get("total_memory_score"), 24 + 20 + 20 + 15)

    def test_object_location_uniqueness_and_variation(self):
        """Verify object location data generates unique icons across rounds without repeats."""
        from .constants import generate_object_location_data

        data1 = generate_object_location_data()
        self.assertEqual(len(data1), 3)

        # Collect all icon IDs across all 3 rounds
        all_icon_ids = []
        for round_items in data1:
            for item in round_items:
                all_icon_ids.append(item["icon"]["id"])

        # Total 3 + 4 + 5 = 12 icons
        self.assertEqual(len(all_icon_ids), 12)
        # All 12 icons must be completely unique
        self.assertEqual(len(set(all_icon_ids)), 12)

        # Generate a second batch and verify it varies
        data2 = generate_object_location_data()
        all_icon_ids_2 = [item["icon"]["id"] for r in data2 for item in r]
        self.assertEqual(len(set(all_icon_ids_2)), 12)

    def test_combined_total_memory_recalculation_when_cached_79_present(self):
        """Verify that total_memory_score dynamically recalculates to 100 when sub-scores sum to 100, even if memory_score was cached as 79 in session."""
        session = self.client.session
        session["memory_score"] = 79  # Old cached default
        session["visual_memory_score"] = 30
        session["recognition_score"] = 25
        session["object_location_score"] = 25
        session.save()

        response = self.client.post(
            reverse("save_delayed_recall"),
            data={"delayed_recall_score": 20},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("total_memory_score"), 100)
        self.assertEqual(data.get("visual_memory_score"), 30)
        self.assertEqual(data.get("recognition_score"), 25)
        self.assertEqual(data.get("object_location_score"), 25)
        self.assertEqual(data.get("delayed_recall_score"), 20)

    def test_recommendations_generation_for_low_scores_and_lifestyle(self):
        """Verify that report context includes personalized recommendations flagging low sleep, high stress, and low game scores."""
        session = self.client.session
        session["name"] = "Low Baseline Test"
        session["sleep_duration"] = 5.0  # Low sleep (< 7h)
        session["stress_level"] = 8      # High stress (>= 7)
        session["exercise_frequency"] = "Low"
        session["screen_time"] = ">8"
        session["reaction_time"] = 450.0 # Slow reaction speed
        session["visual_memory_score"] = 15 # Low visual memory (< 70%)
        session["recognition_score"] = 10    # Low recognition (< 72%)
        session["object_location_score"] = 10 # Low location (< 72%)
        session["delayed_recall_score"] = 8   # Low delayed recall (< 70%)
        session["clock_score"] = 10         # Low CDT (< 75%)
        session.save()

        response = self.client.get(reverse("report"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("lifestyle_recs", response.context)
        self.assertIn("cognitive_recs", response.context)

        lifestyle_categories = [r["category"] for r in response.context["lifestyle_recs"]]
        cognitive_categories = [r["category"] for r in response.context["cognitive_recs"]]

        self.assertIn("Sleep & Recovery", lifestyle_categories)
        self.assertIn("Stress Management", lifestyle_categories)
        self.assertIn("Physical Fitness", lifestyle_categories)
        self.assertIn("Reflex Speed", cognitive_categories)
        self.assertIn("Visual Pattern Memory", cognitive_categories)
        self.assertIn("Delayed Recall", cognitive_categories)





