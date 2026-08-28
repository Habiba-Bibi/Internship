#!/usr/bin/env python3
"""
Integration Tests for FastAPI Internship AI Recommendation Backend
"""

import unittest
from fastapi.testclient import TestClient
from app import app


class TestFastAPIBackend(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Initialize TestClient which runs the lifespan context manager
        cls.client = TestClient(app)

    def test_root_endpoint(self):
        """Test GET / serves the React HTML frontend."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("InternAI", response.text)

    def test_api_index_endpoint(self):
        """Test GET /api returns the JSON API index."""
        response = self.client.get("/api")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("version", data)
        self.assertIn("endpoints", data)

    def test_healthcheck_endpoint(self):
        """Test GET /api/health."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertEqual(data["total_courses"], 37)
        self.assertEqual(data["total_interns"], 600)
        self.assertEqual(data["prerequisite_rules_count"], 3)

    def test_list_interns(self):
        """Test GET /api/interns with pagination and filtering."""
        response = self.client.get("/api/interns?limit=10&offset=0")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_count"], 600)
        self.assertEqual(len(data["interns"]), 10)

        # Test search filter
        search_res = self.client.get("/api/interns?search=INT-0001")
        self.assertEqual(search_res.status_code, 200)
        self.assertGreaterEqual(search_res.json()["total_count"], 1)

    def test_get_single_intern(self):
        """Test GET /api/interns/{intern_id}."""
        response = self.client.get("/api/interns/INT-0001")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("intern_profile", data)
        self.assertEqual(data["intern_profile"]["intern_id"], "INT-0001")

        # Test non-existent intern
        err_res = self.client.get("/api/interns/INT-9999")
        self.assertEqual(err_res.status_code, 404)

    def test_get_intern_history(self):
        """Test GET /api/interns/{intern_id}/history."""
        response = self.client.get("/api/interns/INT-0001/history")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["intern_id"], "INT-0001")
        self.assertGreater(data["total_enrollments"], 0)

    def test_custom_path_recommendation(self):
        """Test POST /api/recommendations/custom-path for existing intern."""
        payload = {
            "intern_id": "INT-0001",
            "roadmap_size": 8
        }
        response = self.client.post("/api/recommendations/custom-path", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["mode"], "existing_intern")
        self.assertEqual(data["intern_id"], "INT-0001")
        roadmap = data["roadmap"]
        self.assertGreater(roadmap["total_courses"], 0)
        self.assertGreater(len(roadmap["phases"]), 0)

    def test_new_intern_path_recommendation(self):
        """Test POST /api/recommendations/new-intern-path for brand-new student."""
        payload = {
            "student_name": "Elena Rostova",
            "target_career_field": "Web & Full-Stack Development",
            "education_level": "Undergraduate Student",
            "academic_major": "Software Engineering",
            "roadmap_size": 8
        }
        response = self.client.post("/api/recommendations/new-intern-path", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["mode"], "new_student_cold_start")
        self.assertEqual(data["intern_name"], "Elena Rostova")
        roadmap = data["roadmap"]
        # Verify first phase is Beginner
        self.assertEqual(roadmap["phases"][0]["difficulty_level"], "Beginner")

    def test_courses_endpoints(self):
        """Test GET /api/courses and single course detail."""
        # List all courses
        response = self.client.get("/api/courses")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_courses"], 37)

        # Get course with prerequisite (CRS-110 requires CRS-108)
        c_res = self.client.get("/api/courses/CRS-110")
        self.assertEqual(c_res.status_code, 200)
        c_data = c_res.json()
        self.assertEqual(c_data["course"]["course_id"], "CRS-110")
        self.assertIsNotNone(c_data["prerequisite"])
        self.assertEqual(c_data["prerequisite"]["course_id"], "CRS-108")

        # Get career fields breakdown
        fields_res = self.client.get("/api/courses/categories/fields")
        self.assertEqual(fields_res.status_code, 200)
        self.assertEqual(fields_res.json()["total_fields"], 6)

        # Get prerequisite rules
        prereq_res = self.client.get("/api/courses/rules/prerequisites")
        self.assertEqual(prereq_res.status_code, 200)
        self.assertEqual(prereq_res.json()["total_rules"], 3)

    def test_model_metrics(self):
        """Test GET /api/model/metrics accuracy scores."""
        response = self.client.get("/api/model/metrics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("test_rmse", data)
        self.assertIn("test_mae", data)
        self.assertIn("matrix_sparsity_percent", data)
        self.assertGreater(data["total_registered_interns"], 0)


if __name__ == "__main__":
    unittest.main()
