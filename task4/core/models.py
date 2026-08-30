from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field
import datetime
import uuid


class Education(BaseModel):
    institution: str = ""
    degree: str = ""
    graduation_year: Optional[Union[int, str]] = None
    gpa: Optional[Union[float, str]] = None
    relevant_coursework: List[str] = Field(default_factory=list)


class ProjectItem(BaseModel):
    title: str
    role: Optional[str] = None
    description: str
    technologies: List[str] = Field(default_factory=list)
    github_url: Optional[str] = None
    live_demo: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)


class ExperienceItem(BaseModel):
    role: str
    organization: str
    period: Optional[str] = None
    description: str


class CandidateProfile(BaseModel):
    id: str = Field(default_factory=lambda: f"cand_{uuid.uuid4().hex[:8]}")
    name: str
    email: Optional[str] = None
    target_role: Optional[str] = None
    education: Optional[Education] = None
    skills: Dict[str, List[str]] = Field(
        default_factory=lambda: {"languages": [], "frameworks": [], "tools": []}
    )
    skill_levels: Dict[str, str] = Field(default_factory=dict)
    projects: List[ProjectItem] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    growth_areas: List[str] = Field(default_factory=list)
    raw_resume_text: Optional[str] = None

    def get_all_skills_flat(self) -> List[str]:
        all_s = []
        for cat, slist in self.skills.items():
            if isinstance(slist, list):
                all_s.extend(slist)
        for s in self.skill_levels.keys():
            if s not in all_s:
                all_s.append(s)
        for proj in self.projects:
            for tech in proj.technologies:
                if tech not in all_s:
                    all_s.append(tech)
        return list(dict.fromkeys(all_s))


class JobDescription(BaseModel):
    id: str = Field(default_factory=lambda: f"job_{uuid.uuid4().hex[:8]}")
    title: str
    department: Optional[str] = None
    level: str = "Internship / Co-op"
    duration: Optional[str] = "12 Weeks"
    location: Optional[str] = "Hybrid / Remote"
    company_overview: Optional[str] = None
    responsibilities: List[str] = Field(default_factory=list)
    required_skills: List[str] = Field(default_factory=list)
    preferred_skills: List[str] = Field(default_factory=list)
    cultural_competencies: List[str] = Field(default_factory=list)
    raw_job_text: Optional[str] = None


class RubricCriteria(BaseModel):
    poor: str = "Shows fundamental misunderstandings or inability to explain basic concepts."
    good: str = "Correctly answers the question, explains key trade-offs, and provides reasonable reasoning."
    excellent: str = "Demonstrates deep mastery, structured communication, edge case awareness, and proactive insights."


class QuestionItem(BaseModel):
    id: str = Field(default_factory=lambda: f"Q-{uuid.uuid4().hex[:6].upper()}")
    category: str = "Technical"  # Technical, Behavioral, Resume Deep Dive, Situational / Scenario
    domain: str = "General Engineering"
    skills: List[str] = Field(default_factory=list)
    difficulty: str = "Standard Intern"  # Foundational, Standard Intern, Advanced Intern
    question: str
    context: str = ""
    expected_key_points: List[str] = Field(default_factory=list)
    follow_up_probes: List[str] = Field(default_factory=list)
    rubric: RubricCriteria = Field(default_factory=RubricCriteria)
    time_allocation_mins: int = 5
    project_reference: Optional[str] = None
    is_custom_generated: bool = False


class SkillGapAnalysis(BaseModel):
    matched_skills: List[str] = Field(default_factory=list)
    missing_required_skills: List[str] = Field(default_factory=list)
    missing_preferred_skills: List[str] = Field(default_factory=list)
    candidate_unique_strengths: List[str] = Field(default_factory=list)
    match_score_percentage: float = 0.0
    recommended_focus_areas: List[str] = Field(default_factory=list)


class InterviewSection(BaseModel):
    title: str
    duration_mins: int
    description: str
    questions: List[QuestionItem] = Field(default_factory=list)


class InterviewKit(BaseModel):
    id: str = Field(default_factory=lambda: f"kit_{uuid.uuid4().hex[:8]}")
    candidate_id: str
    candidate_name: str
    job_id: str
    job_title: str
    generated_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    total_duration_mins: int = 45
    target_level: str = "Intern"
    skill_analysis: SkillGapAnalysis = Field(default_factory=SkillGapAnalysis)
    sections: List[InterviewSection] = Field(default_factory=list)
    questions: List[QuestionItem] = Field(default_factory=list)
    interviewer_notes_template: str = ""


class ScorecardRating(BaseModel):
    question_id: str
    score: int = Field(ge=1, le=5)  # 1: Poor, 2: Marginal, 3: Competent/Good, 4: Strong, 5: Outstanding
    notes: str = ""
    evaluated_at: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())


class Scorecard(BaseModel):
    id: str = Field(default_factory=lambda: f"sc_{uuid.uuid4().hex[:8]}")
    kit_id: str
    candidate_name: str
    job_title: str
    interviewer_name: str = "Interviewer"
    date: str = Field(default_factory=lambda: datetime.datetime.now().strftime("%Y-%m-%d"))
    ratings: List[ScorecardRating] = Field(default_factory=list)
    overall_score: float = 0.0
    recommendation: str = "Undecided"  # Strong Hire, Hire, Leaning Hire, Leaning No Hire, No Hire
    final_feedback: str = ""


class GenerationRequest(BaseModel):
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    custom_candidate: Optional[CandidateProfile] = None
    custom_job: Optional[JobDescription] = None
    raw_resume_text: Optional[str] = None
    raw_job_text: Optional[str] = None
    num_technical: int = 4
    num_behavioral: int = 3
    num_resume_deep_dive: int = 2
    num_scenario: int = 1
    difficulty: str = "Standard Intern"  # Foundational, Standard Intern, Advanced Intern, Mixed
    llm_provider: str = "mock"  # mock, openai, llama, groq, custom
    model_name: Optional[str] = None
    api_key: Optional[str] = None
    temperature: float = 0.7
    focus_skills: List[str] = Field(default_factory=list)
