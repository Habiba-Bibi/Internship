import unittest
from core.models import (
    CandidateProfile,
    Education,
    ProjectItem,
    JobDescription,
    QuestionItem,
    RubricCriteria,
    Scorecard,
    ScorecardRating,
)


class TestModels(unittest.TestCase):
    def test_candidate_profile_creation(self):
        cand = CandidateProfile(
            name="Jane Doe",
            education=Education(institution="Tech Univ", degree="B.S. CS", gpa=3.9),
            skills={"languages": ["Python", "Go"], "frameworks": ["FastAPI"]},
            projects=[
                ProjectItem(
                    title="Distributed KV Store",
                    description="Built Raft-based consensus store in Go.",
                    technologies=["Go", "Raft", "gRPC"],
                )
            ],
        )
        self.assertEqual(cand.name, "Jane Doe")
        all_skills = cand.get_all_skills_flat()
        self.assertIn("Python", all_skills)
        self.assertIn("Go", all_skills)
        self.assertIn("FastAPI", all_skills)
        self.assertIn("gRPC", all_skills)

    def test_job_description_creation(self):
        job = JobDescription(
            title="Backend Intern",
            required_skills=["Python", "SQL", "REST API"],
            preferred_skills=["Docker", "Redis"],
        )
        self.assertEqual(job.title, "Backend Intern")
        self.assertEqual(len(job.required_skills), 3)

    def test_question_item_rubric(self):
        q = QuestionItem(
            question="What is the difference between SQL and NoSQL?",
            category="Technical",
            domain="Databases",
            rubric=RubricCriteria(
                poor="Cannot explain basic schemas.",
                good="Explains ACID vs BASE.",
                excellent="Details distributed consistency and indexing.",
            ),
        )
        self.assertEqual(q.category, "Technical")
        self.assertEqual(q.rubric.good, "Explains ACID vs BASE.")


if __name__ == "__main__":
    unittest.main()
