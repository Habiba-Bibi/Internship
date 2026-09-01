"""
test_pipeline.py
Comprehensive automated test suite for Intern Skills Analysis,
NLP TF-IDF Vectorization, K-Means Clustering, Gap Calculation, and Flask REST APIs.
"""

import os
import sys
import unittest
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.nlp_clustering_pipeline import SkillGapClusteringEngine, clean_tech_text
from src.app import app


class TestSkillGapPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = SkillGapClusteringEngine(n_clusters=8)
        cls.engine.load_artifacts()

    def test_datasets_exist_and_valid(self):
        """Checks if all required datasets are present and non-empty."""
        self.assertIsNotNone(self.engine.interns_df)
        self.assertIsNotNone(self.engine.jobs_df)
        self.assertGreater(len(self.engine.interns_df), 300)
        self.assertGreater(len(self.engine.jobs_df), 500)
        self.assertGreater(len(self.engine.course_catalog), 30)
        self.assertGreater(len(self.engine.skills_taxonomy), 80)

    def test_text_cleaning_tech_preservation(self):
        """Verifies special technical tokens are retained during cleaning."""
        sample = "We need C++, Node.js, and CI/CD with TCP/IP experience!"
        cleaned = clean_tech_text(sample)
        self.assertIn("cplusplus", cleaned)
        self.assertIn("nodejs", cleaned)
        self.assertIn("cicd", cleaned)
        self.assertIn("tcpip", cleaned)

    def test_tfidf_and_clustering(self):
        """Verifies TF-IDF vectorizer and K-Means cluster count."""
        self.assertIsNotNone(self.engine.vectorizer)
        self.assertIsNotNone(self.engine.kmeans)
        self.assertEqual(self.engine.kmeans.n_clusters, 8)
        self.assertEqual(len(self.engine.cluster_profiles), 8)

        # Check PCA output
        self.assertEqual(self.engine.job_pca_coords.shape[1], 2)
        self.assertEqual(self.engine.intern_pca_coords.shape[1], 2)

    def test_intern_gap_analysis(self):
        """Verifies intern skill gap calculation and readiness score bounds."""
        res = self.engine.analyze_intern_by_id("INT-1001")
        self.assertIsNotNone(res)
        self.assertEqual(res["intern_id"], "INT-1001")

        gap = res["gap_analysis"]
        self.assertIn("readiness_score", gap)
        self.assertGreaterEqual(gap["readiness_score"], 0)
        self.assertLessEqual(gap["readiness_score"], 100)
        self.assertIsInstance(gap["matched_skills"], list)
        self.assertIsInstance(gap["missing_critical_skills"], list)

        # Training plan
        tp = gap["training_plan"]
        self.assertEqual(len(tp["phases"]), 3)
        self.assertGreater(tp["estimated_study_hours"], 0)

    def test_custom_profile_analysis(self):
        """Verifies live custom skills analysis on-the-fly."""
        custom_res = self.engine.analyze_custom_profile(
            skills_input="Python, PyTorch, Deep Learning, scikit-learn",
            target_role="Machine Learning Engineer",
            bio_input="CS Master student passionate about deep learning and computer vision."
        )
        self.assertIsNotNone(custom_res)
        self.assertIn("gap_analysis", custom_res)
        self.assertIn("readiness_score", custom_res["gap_analysis"])
        self.assertEqual(len(custom_res["pca_coords"]), 2)


class TestFlaskAPIServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def test_index_route(self):
        """Verifies the main dashboard HTML page loads."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"SkillBridge", response.data)

    def test_api_overview(self):
        """Verifies market overview API."""
        response = self.client.get("/api/overview")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("summary_metrics", data["data"])
        self.assertIn("skill_gap_comparison", data["data"])

    def test_api_clusters(self):
        """Verifies cluster intelligence API."""
        response = self.client.get("/api/clusters")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("clusters", data["data"])
        self.assertIn("jobs_scatter", data["data"])
        self.assertIn("interns_scatter", data["data"])

    def test_api_interns_list_and_detail(self):
        """Verifies interns directory and individual detail API."""
        response = self.client.get("/api/interns?domain=AI%20%26%20Machine%20Learning")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertGreater(data["total"], 0)

        # Detail route
        intern_id = data["data"][0]["intern_id"]
        detail_resp = self.client.get(f"/api/intern/{intern_id}")
        self.assertEqual(detail_resp.status_code, 200)
        detail_data = json.loads(detail_resp.data)
        self.assertEqual(detail_data["status"], "success")
        self.assertIn("radar_chart", detail_data["data"])
        self.assertIn("training_plan", detail_data["data"]["gap_analysis"])

    def test_api_jobs_list(self):
        """Verifies industry jobs list API."""
        response = self.client.get("/api/jobs")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total"], 650)

    def test_api_analyze_custom(self):
        """Verifies custom simulator POST API."""
        payload = {
            "skills": "JavaScript, React, Node.js, Git, HTML5, CSS3",
            "target_role": "Full Stack Developer",
            "bio": "Self-taught web developer with portfolio in React apps."
        }
        response = self.client.post("/api/analyze-custom", json=payload)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertIn("gap_analysis", data["data"])
        self.assertIn("radar_chart", data["data"])

    def test_api_courses(self):
        """Verifies course catalog API."""
        response = self.client.get("/api/courses")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "success")
        self.assertGreaterEqual(len(data["data"]), 35)


if __name__ == "__main__":
    unittest.main()
