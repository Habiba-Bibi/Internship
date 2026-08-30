import unittest
from fastapi.testclient import TestClient
from server import app


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_list_candidates(self):
        resp = self.client.get("/api/candidates")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

    def test_list_jobs(self):
        resp = self.client.get("/api/jobs")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)

    def test_search_questions(self):
        resp = self.client.get("/api/questions?category=Technical")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIsInstance(data, list)
        self.assertTrue(all(q["category"] == "Technical" for q in data))

    def test_generate_kit_and_export(self):
        # Fetch first candidate & job
        cands = self.client.get("/api/candidates").json()
        jobs = self.client.get("/api/jobs").json()

        payload = {
            "candidate_id": cands[0]["id"],
            "job_id": jobs[0]["id"],
            "num_technical": 2,
            "num_behavioral": 2,
            "num_resume_deep_dive": 1,
            "num_scenario": 1,
            "difficulty": "Standard Intern",
            "llm_provider": "mock",
        }
        resp = self.client.post("/api/generate-kit", json=payload)
        self.assertEqual(resp.status_code, 200)
        kit_data = resp.json()
        self.assertIn("id", kit_data)
        kit_id = kit_data["id"]

        # Test Export Markdown
        exp_md = self.client.get(f"/api/export/{kit_id}?format=markdown")
        self.assertEqual(exp_md.status_code, 200)
        self.assertIn("Intern Interview Guide", exp_md.text)

        # Test Export HTML
        exp_html = self.client.get(f"/api/export/{kit_id}?format=html")
        self.assertEqual(exp_html.status_code, 200)
        self.assertIn("<!DOCTYPE html>", exp_html.text)

    def test_submit_scorecard(self):
        scorecard_payload = {
            "kit_id": "kit_test123",
            "candidate_name": "Alex Chen",
            "job_title": "Frontend Intern",
            "interviewer_name": "Lead Interviewer",
            "ratings": [
                {"question_id": "Q-01", "score": 5, "notes": "Great explanation"},
                {"question_id": "Q-02", "score": 4, "notes": "Solid understanding"},
                {"question_id": "Q-03", "score": 5, "notes": "Outstanding depth"},
            ],
        }
        resp = self.client.post("/api/scorecard", json=scorecard_payload)
        self.assertEqual(resp.status_code, 200)
        sc = resp.json()
        self.assertGreaterEqual(sc["overall_score"], 4.0)
        self.assertIn(sc["recommendation"], ["Strong Hire", "Hire"])


if __name__ == "__main__":
    unittest.main()
