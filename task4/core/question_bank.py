import json
import os
from typing import List, Optional, Dict, Any
from core.models import QuestionItem, RubricCriteria


class QuestionBank:
    """Manages the repository of curated interview questions."""

    def __init__(self, data_path: Optional[str] = None):
        if data_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_path = os.path.join(base_dir, "data", "question_bank.json")
        self.data_path = data_path
        self.questions: List[QuestionItem] = []
        self.load()

    def load(self) -> None:
        """Load questions from disk."""
        if not os.path.exists(self.data_path):
            self.questions = []
            return

        with open(self.data_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            self.questions = []
            for item in raw_data:
                rubric_data = item.get("rubric", {})
                rubric_obj = RubricCriteria(
                    poor=rubric_data.get("poor", ""),
                    good=rubric_data.get("good", ""),
                    excellent=rubric_data.get("excellent", ""),
                )
                q = QuestionItem(
                    id=item.get("id", ""),
                    category=item.get("category", "Technical"),
                    domain=item.get("domain", "General Engineering"),
                    skills=item.get("skills", []),
                    difficulty=item.get("difficulty", "Standard Intern"),
                    question=item.get("question", ""),
                    context=item.get("context", ""),
                    expected_key_points=item.get("expected_key_points", []),
                    follow_up_probes=item.get("follow_up_probes", []),
                    rubric=rubric_obj,
                    time_allocation_mins=item.get("time_allocation_mins", 5),
                )
                self.questions.append(q)

    def save(self) -> None:
        """Save current questions back to disk."""
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        raw = []
        for q in self.questions:
            raw.append(
                {
                    "id": q.id,
                    "category": q.category,
                    "domain": q.domain,
                    "skills": q.skills,
                    "difficulty": q.difficulty,
                    "question": q.question,
                    "context": q.context,
                    "expected_key_points": q.expected_key_points,
                    "follow_up_probes": q.follow_up_probes,
                    "rubric": {
                        "poor": q.rubric.poor,
                        "good": q.rubric.good,
                        "excellent": q.rubric.excellent,
                    },
                    "time_allocation_mins": q.time_allocation_mins,
                }
            )
        with open(self.data_path, "w", encoding="utf-8") as f:
            json.dump(raw, f, indent=2)

    def get_all(self) -> List[QuestionItem]:
        return self.questions

    def get_by_id(self, qid: str) -> Optional[QuestionItem]:
        for q in self.questions:
            if q.id == qid:
                return q
        return None

    def filter(
        self,
        category: Optional[str] = None,
        domain: Optional[str] = None,
        skill: Optional[str] = None,
        difficulty: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> List[QuestionItem]:
        """Filter questions based on multiple criteria."""
        results = self.questions

        if category and category.lower() != "all":
            results = [q for q in results if q.category.lower() == category.lower()]

        if domain and domain.lower() != "all":
            results = [q for q in results if domain.lower() in q.domain.lower()]

        if skill and skill.lower() != "all":
            results = [
                q
                for q in results
                if any(skill.lower() in s.lower() for s in q.skills)
            ]

        if difficulty and difficulty.lower() != "all" and difficulty.lower() != "mixed":
            results = [
                q for q in results if q.difficulty.lower() == difficulty.lower()
            ]

        if search_query:
            sq = search_query.lower()
            results = [
                q
                for q in results
                if sq in q.question.lower()
                or sq in q.context.lower()
                or any(sq in s.lower() for s in q.skills)
                or sq in q.domain.lower()
            ]

        return results

    def find_relevant_questions(
        self,
        target_skills: List[str],
        category: str = "Technical",
        difficulty: Optional[str] = None,
        limit: int = 5,
    ) -> List[QuestionItem]:
        """
        Retrieve and rank questions matching target skills using a relevance scoring metric.
        """
        candidates = [q for q in self.questions if q.category.lower() == category.lower()]
        if difficulty and difficulty.lower() not in ["all", "mixed"]:
            candidates = [
                q for q in candidates if q.difficulty.lower() == difficulty.lower()
            ]

        target_set = {s.lower() for s in target_skills}

        scored = []
        for q in candidates:
            score = 0
            for q_skill in q.skills:
                q_skill_lower = q_skill.lower()
                if q_skill_lower in target_set:
                    score += 3
                elif any(q_skill_lower in ts or ts in q_skill_lower for ts in target_set):
                    score += 1

            scored.append((score, q))

        # Sort descending by score
        scored.sort(key=lambda x: x[0], reverse=True)
        return [q for score, q in scored[:limit]]

    def add_question(self, question: QuestionItem) -> None:
        self.questions.append(question)
        self.save()
