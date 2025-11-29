# backend/tasks/tests.py
import json
from datetime import datetime, timedelta, timezone

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .scoring import analyze_tasks


class ScoringUnitTests(TestCase):
    def test_overdue_task_scores_higher_than_future_task(self):
        """
        Assert the intended behavior: an overdue task should score higher
        than the same task when it's not overdue.
        """
        today = datetime.now(timezone.utc).date()

        overdue = {
            "id": "overdue",
            "title": "Overdue Task",
            "due_date": (today - timedelta(days=2)).isoformat(),
            "estimated_hours": 2,
            "importance": 5,
            "dependencies": []
        }

        future = {
            "id": "future",
            "title": "Future Task",
            "due_date": (today + timedelta(days=10)).isoformat(),
            "estimated_hours": 2,
            "importance": 5,
            "dependencies": []
        }

        result = analyze_tasks([overdue, future], today=today)
        sorted_list = result.get("sorted", [])
        self.assertEqual(len(sorted_list), 2)

        scores = {t["id"]: t["score"] for t in sorted_list}
        self.assertIn("overdue", scores)
        self.assertIn("future", scores)
        self.assertGreater(
            scores["overdue"],
            scores["future"],
            msg=f"Expected overdue score > future score but got overdue={scores['overdue']} future={scores['future']}"
        )

    def test_cycle_detection(self):
        t1 = {"id": "A", "title": "A", "dependencies": ["B"]}
        t2 = {"id": "B", "title": "B", "dependencies": ["A"]}

        result = analyze_tasks([t1, t2])

        self.assertIsNotNone(result.get("cycle"))
        self.assertTrue(len(result["cycle"]) >= 2)

    def test_missing_fields_handled(self):
        task = {"title": "No ID or Dates"}
        result = analyze_tasks([task])

        self.assertIn("sorted", result)
        self.assertEqual(len(result["sorted"]), 1)
        self.assertIn("score", result["sorted"][0])


class EndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_analyze_endpoint_valid(self):
        url = reverse("tasks:analyze")
        tasks = [
            {
                "id": "1",
                "title": "T1",
                "due_date": None,
                "estimated_hours": 1,
                "importance": 9,
                "dependencies": []
            }
        ]

        response = self.client.post(url, {"tasks": tasks}, format="json")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("sorted", data)
        self.assertEqual(len(data["sorted"]), 1)

    def test_analyze_bad_payload(self):
        url = reverse("tasks:analyze")

        response = self.client.post(url, {"wrong_key": "bad"}, format="json")
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn("errors", data)

    def test_suggest_endpoint_get(self):
        url = reverse("tasks:suggest")

        tasks = [
            {"id": "1", "title": "A", "estimated_hours": 1, "importance": 9, "dependencies": [], "due_date": None},
            {"id": "2", "title": "B", "estimated_hours": 5, "importance": 2, "dependencies": [], "due_date": None},
            {"id": "3", "title": "C", "estimated_hours": 3, "importance": 5, "dependencies": [], "due_date": None}
        ]

        encoded = json.dumps(tasks)
        response = self.client.get(url, {"tasks": encoded})
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("suggestions", data)
        self.assertLessEqual(len(data["suggestions"]), 3)

        first = data["suggestions"][0]
        self.assertIn("id", first)
        self.assertIn("title", first)
        self.assertIn("score", first)
        self.assertIn("reason", first)
        self.assertIn("task", first)

    def test_suggest_endpoint_get_bad_json(self):
        """
        Pass intentionally invalid JSON in the 'tasks' query param.
        """
        url = reverse("tasks:suggest")
        bad_json = "not-a-valid-json"

        response = self.client.get(url, {"tasks": bad_json})
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "invalid JSON in tasks parameter")

    def test_suggest_missing_param(self):
        """
        Call the suggest endpoint without the 'tasks' parameter.
        """
        url = reverse("tasks:suggest")

        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(
            data["error"],
            "missing tasks parameter. Use POST /api/tasks/analyze/ instead."
        )
