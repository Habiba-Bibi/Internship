import unittest
from core.models import CandidateProfile, JobDescription, ProjectItem
from core.matcher import analyze_skill_gap, extract_skills_from_text, normalize_skill


class TestMatcher(unittest.TestCase):
    def test_skill_normalization(self):
        self.assertEqual(normalize_skill("js"), "JavaScript")
        self.assertEqual(normalize_skill("JavaScript (ES6+)"), "JavaScript")
        self.assertEqual(normalize_skill("k8s"), "Kubernetes")
        self.assertEqual(normalize_skill("postgres"), "PostgreSQL")

    def test_text_skill_extraction(self):
        text = "We are seeking an intern proficient in React, TypeScript, and Docker containerization."
        extracted = extract_skills_from_text(text)
        self.assertIn("React", extracted)
        self.assertIn("TypeScript", extracted)
        self.assertIn("Docker", extracted)

    def test_analyze_skill_gap_high_match(self):
        cand = CandidateProfile(
            name="Alex Frontend",
            skills={"languages": ["JavaScript", "TypeScript"], "frameworks": ["React", "Next.js"]},
            projects=[
                ProjectItem(
                    title="React Dashboard",
                    description="Built frontend in React and CSS Grid.",
                    technologies=["React", "TypeScript", "TailwindCSS"],
                )
            ],
        )
        job = JobDescription(
            title="Frontend Intern",
            required_skills=["JavaScript", "React"],
            preferred_skills=["TypeScript", "Next.js"],
        )
        analysis = analyze_skill_gap(cand, job)
        self.assertGreaterEqual(analysis.match_score_percentage, 80.0)
        self.assertIn("JavaScript", analysis.matched_skills)
        self.assertIn("React", analysis.matched_skills)
        self.assertEqual(len(analysis.missing_required_skills), 0)

    def test_analyze_skill_gap_with_missing_skills(self):
        cand = CandidateProfile(
            name="Python Student",
            skills={"languages": ["Python"], "frameworks": ["Django"]},
        )
        job = JobDescription(
            title="DevOps Intern",
            required_skills=["Docker", "Kubernetes", "Terraform"],
            preferred_skills=["AWS", "Python"],
        )
        analysis = analyze_skill_gap(cand, job)
        self.assertIn("Docker", analysis.missing_required_skills)
        self.assertIn("Kubernetes", analysis.missing_required_skills)
        self.assertIn("Python", analysis.matched_skills)


if __name__ == "__main__":
    unittest.main()
