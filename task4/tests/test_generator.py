import unittest
import asyncio
from core.models import CandidateProfile, JobDescription, ProjectItem, GenerationRequest
from core.generator import InterviewQuestionGenerator
from core.exporter import KitExporter


class TestGenerator(unittest.TestCase):
    def setUp(self):
        self.generator = InterviewQuestionGenerator()
        self.candidate = CandidateProfile(
            name="Marcus Vance",
            skills={"languages": ["Python", "Go"], "frameworks": ["FastAPI", "Django"]},
            projects=[
                ProjectItem(
                    title="HyperQueue Broker",
                    description="Distributed task queue in Go and Redis with heartbeat checks.",
                    technologies=["Go", "Redis", "Docker"],
                )
            ],
        )
        self.job = JobDescription(
            title="Backend Engineering Intern",
            required_skills=["Python", "FastAPI", "SQL"],
            preferred_skills=["Docker", "Redis"],
        )

    def test_generate_interview_kit(self):
        async def _test():
            req = GenerationRequest(
                custom_candidate=self.candidate,
                custom_job=self.job,
                num_technical=3,
                num_behavioral=2,
                num_resume_deep_dive=1,
                num_scenario=1,
                difficulty="Standard Intern",
                llm_provider="mock",
            )
            kit = await self.generator.generate_interview_kit(req)
            self.assertEqual(kit.candidate_name, "Marcus Vance")
            self.assertEqual(kit.job_title, "Backend Engineering Intern")
            self.assertTrue(len(kit.sections) >= 4)
            self.assertTrue(len(kit.questions) >= 5)

            # Test Exporters
            md = KitExporter.to_markdown(kit)
            self.assertIn("Intern Interview Guide", md)
            self.assertIn("HyperQueue Broker", md)

            html = KitExporter.to_html(kit)
            self.assertIn("<!DOCTYPE html>", html)
            self.assertIn("Marcus Vance", html)

            json_str = KitExporter.to_json(kit)
            self.assertIn('"candidate_name": "Marcus Vance"', json_str)

        asyncio.run(_test())

    def test_regenerate_question(self):
        async def _test():
            q = await self.generator.regenerate_single_question(
                category="Technical",
                domain="Backend",
                skill="Redis",
                difficulty="Standard Intern",
            )
            self.assertIsNotNone(q)
            self.assertEqual(q.category, "Technical")

        asyncio.run(_test())


if __name__ == "__main__":
    unittest.main()
