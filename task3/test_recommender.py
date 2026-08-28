#!/usr/bin/env python3
"""
Unit and Integration Tests for Internship Recommendation Engine
"""

import unittest
from pathlib import Path
from recommender import DataLoader, MatrixFactorizationSVD, ColdStartEngine, RoadmapGenerator, InternshipRecommender


class TestInternshipRecommender(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = InternshipRecommender(data_dir="data")
        cls.metrics = cls.engine.train(verbose=False)

    def test_data_loader(self):
        """Test dataset loading integrity."""
        dl = self.engine.dl
        self.assertEqual(len(dl.courses), 37, "Must load exactly 37 courses")
        self.assertEqual(len(dl.interns), 600, "Must load exactly 600 interns")
        self.assertEqual(len(dl.prerequisites), 3, "Must load 3 prerequisite rules")
        self.assertGreater(len(dl.ratings_data), 5000, "Must load ratings data")

    def test_cf_model_convergence_and_metrics(self):
        """Test that CF model trains and achieves acceptable RMSE."""
        self.assertLess(self.metrics["rmse"], 1.50, "RMSE should be within realistic accuracy bounds")
        self.assertLess(self.metrics["mae"], 1.20, "MAE should be within realistic accuracy bounds")

        # Test prediction bounds
        pred = self.engine.cf_model.predict("INT-0001", "CRS-101")
        self.assertTrue(1.0 <= pred <= 5.0, f"Predicted rating {pred} must be between 1.0 and 5.0")

    def test_existing_intern_roadmap(self):
        """Test roadmap for existing intern: no completed courses, strict prerequisites."""
        res = self.engine.recommend_for_intern("INT-0001", roadmap_size=8)
        roadmap = res["roadmap"]
        completed = set(res["past_completed_course_ids"])

        all_steps = []
        for phase in roadmap["phases"]:
            for step in phase["steps"]:
                all_steps.append(step)

        # 1. Verify no completed course is in roadmap
        for step in all_steps:
            self.assertNotIn(step["course_id"], completed, f"Completed course {step['course_id']} should not be in roadmap")

        # 2. Verify topological prerequisite order
        course_indices = {step["course_id"]: idx for idx, step in enumerate(all_steps)}
        for step in all_steps:
            cid = step["course_id"]
            if cid in self.engine.dl.prerequisites:
                prereq_id = self.engine.dl.prerequisites[cid]
                # If prereq was not in past completed courses, it MUST be in roadmap and before this step!
                if prereq_id not in completed:
                    self.assertIn(prereq_id, course_indices, f"Prerequisite {prereq_id} for {cid} must be in roadmap")
                    self.assertLess(course_indices[prereq_id], course_indices[cid],
                                   f"Prerequisite {prereq_id} must appear before dependent course {cid}")

        # 3. Verify difficulty level ordering (Beginner -> Intermediate -> Advanced)
        level_map = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
        current_max_level = 1
        for step in all_steps:
            lvl = level_map[step["difficulty_level"]]
            self.assertGreaterEqual(lvl, current_max_level, "Difficulty level must not regress backwards")
            current_max_level = max(current_max_level, lvl)

    def test_cold_start_new_student(self):
        """Test brand-new student with no history."""
        res = self.engine.recommend_for_new_student(
            student_name="Jane Doe",
            target_career_field="Data Science & Artificial Intelligence",
            education_level="Undergraduate Student",
            academic_major="Mathematics",
            roadmap_size=8
        )
        roadmap = res["roadmap"]
        self.assertEqual(res["past_courses_completed_count"], 0)

        all_steps = []
        for phase in roadmap["phases"]:
            for step in phase["steps"]:
                all_steps.append(step)

        self.assertGreater(len(all_steps), 0)

        # Check that the first phase starts with Beginner
        self.assertEqual(roadmap["phases"][0]["difficulty_level"], "Beginner")

        # Verify that Data Science & AI courses are prominent
        field_matches = sum(1 for s in all_steps if s["career_field"] == "Data Science & Artificial Intelligence")
        self.assertGreaterEqual(field_matches, 3, "New student should receive courses matching their chosen track")

        # Verify prerequisite ordering for new student
        course_indices = {step["course_id"]: idx for idx, step in enumerate(all_steps)}
        for step in all_steps:
            cid = step["course_id"]
            if cid in self.engine.dl.prerequisites:
                prereq_id = self.engine.dl.prerequisites[cid]
                self.assertIn(prereq_id, course_indices, f"Prerequisite {prereq_id} for {cid} must be injected for new student")
                self.assertLess(course_indices[prereq_id], course_indices[cid],
                               f"Prerequisite {prereq_id} must be placed before {cid}")

    def test_all_prerequisite_rules_in_system(self):
        """Verify the 3 explicit prerequisite rules in catalogue."""
        prereqs = self.engine.dl.prerequisites
        self.assertEqual(prereqs.get("CRS-110"), "CRS-108", "Rule 1: CRS-108 -> CRS-110")
        self.assertEqual(prereqs.get("CRS-103"), "CRS-102", "Rule 2: CRS-102 -> CRS-103")
        self.assertEqual(prereqs.get("CRS-117"), "CRS-115", "Rule 3: CRS-115 -> CRS-117")


if __name__ == "__main__":
    unittest.main()
