import os
import json
import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import PlainTextResponse, HTMLResponse, Response

from core.models import (
    CandidateProfile,
    JobDescription,
    QuestionItem,
    InterviewKit,
    Scorecard,
    ScorecardRating,
    GenerationRequest,
    SkillGapAnalysis,
)
from core.matcher import analyze_skill_gap
from core.question_bank import QuestionBank
from core.generator import InterviewQuestionGenerator
from core.exporter import KitExporter

router = APIRouter(prefix="/api")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
CANDIDATES_DIR = os.path.join(DATA_DIR, "candidates")
JOBS_DIR = os.path.join(DATA_DIR, "jobs")

question_bank = QuestionBank()
generator = InterviewQuestionGenerator(question_bank)

# In-memory storage for active generated kits and scorecards
KITS_CACHE: Dict[str, InterviewKit] = {}
SCORECARDS_CACHE: Dict[str, Scorecard] = {}


def _load_candidates() -> List[CandidateProfile]:
    candidates = []
    if os.path.exists(CANDIDATES_DIR):
        for fname in os.listdir(CANDIDATES_DIR):
            if fname.endswith(".json"):
                fpath = os.path.join(CANDIDATES_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        candidates.append(CandidateProfile.model_validate(data))
                except Exception as e:
                    print(f"Error loading candidate {fname}: {e}")
    return candidates


def _load_jobs() -> List[JobDescription]:
    jobs = []
    if os.path.exists(JOBS_DIR):
        for fname in os.listdir(JOBS_DIR):
            if fname.endswith(".json"):
                fpath = os.path.join(JOBS_DIR, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        jobs.append(JobDescription.model_validate(data))
                except Exception as e:
                    print(f"Error loading job {fname}: {e}")
    return jobs


@router.get("/candidates", response_model=List[CandidateProfile])
def list_candidates():
    """List all available candidate profiles."""
    return _load_candidates()


@router.get("/candidates/{candidate_id}", response_model=CandidateProfile)
def get_candidate(candidate_id: str):
    """Retrieve a single candidate profile by ID."""
    for c in _load_candidates():
        if c.id == candidate_id:
            return c
    raise HTTPException(status_code=404, detail="Candidate not found")


@router.post("/candidates", response_model=CandidateProfile)
def create_candidate(candidate: CandidateProfile):
    """Save a new candidate profile."""
    os.makedirs(CANDIDATES_DIR, exist_ok=True)
    filename = f"{candidate.id}.json"
    filepath = os.path.join(CANDIDATES_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(candidate.model_dump_json(indent=2))
    return candidate


@router.get("/jobs", response_model=List[JobDescription])
def list_jobs():
    """List all available job descriptions."""
    return _load_jobs()


@router.get("/jobs/{job_id}", response_model=JobDescription)
def get_job(job_id: str):
    """Retrieve a single job description by ID."""
    for j in _load_jobs():
        if j.id == job_id:
            return j
    raise HTTPException(status_code=404, detail="Job description not found")


@router.post("/jobs", response_model=JobDescription)
def create_job(job: JobDescription):
    """Save a new job description."""
    os.makedirs(JOBS_DIR, exist_ok=True)
    filename = f"{job.id}.json"
    filepath = os.path.join(JOBS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(job.model_dump_json(indent=2))
    return job


@router.get("/questions", response_model=List[QuestionItem])
def search_questions(
    category: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
):
    """Search and filter question bank."""
    return question_bank.filter(
        category=category,
        domain=domain,
        skill=skill,
        difficulty=difficulty,
        search_query=q,
    )


@router.post("/questions", response_model=QuestionItem)
def add_question(question: QuestionItem):
    """Add a new question to the bank."""
    question_bank.add_question(question)
    return question


@router.post("/match-analysis", response_model=SkillGapAnalysis)
def perform_match_analysis(
    candidate_id: Optional[str] = Body(None),
    job_id: Optional[str] = Body(None),
    custom_candidate: Optional[CandidateProfile] = Body(None),
    custom_job: Optional[JobDescription] = Body(None),
):
    """Analyze skill gap and alignment between a candidate and a job."""
    # Find candidate
    cand_obj = None
    if custom_candidate:
        cand_obj = custom_candidate
    elif candidate_id:
        for c in _load_candidates():
            if c.id == candidate_id:
                cand_obj = c
                break

    # Find job
    job_obj = None
    if custom_job:
        job_obj = custom_job
    elif job_id:
        for j in _load_jobs():
            if j.id == job_id:
                job_obj = j
                break

    if not cand_obj or not job_obj:
        raise HTTPException(status_code=400, detail="Candidate and Job required for analysis")

    return analyze_skill_gap(cand_obj, job_obj)


@router.post("/generate-kit", response_model=InterviewKit)
async def generate_interview_kit(request: GenerationRequest):
    """Generate a custom, structured interview question kit."""
    # If candidate_id given, resolve profile
    if request.candidate_id and not request.custom_candidate:
        for c in _load_candidates():
            if c.id == request.candidate_id:
                request.custom_candidate = c
                break

    # If job_id given, resolve job
    if request.job_id and not request.custom_job:
        for j in _load_jobs():
            if j.id == request.job_id:
                request.custom_job = j
                break

    try:
        kit = await generator.generate_interview_kit(request)
        KITS_CACHE[kit.id] = kit
        return kit
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/kits/{kit_id}", response_model=InterviewKit)
def get_interview_kit(kit_id: str):
    """Retrieve cached interview kit."""
    if kit_id not in KITS_CACHE:
        raise HTTPException(status_code=404, detail="Interview kit not found")
    return KITS_CACHE[kit_id]


@router.post("/regenerate-question", response_model=QuestionItem)
async def regenerate_question(
    category: str = Body("Technical"),
    domain: str = Body("General Engineering"),
    skill: str = Body("JavaScript"),
    difficulty: str = Body("Standard Intern"),
    candidate_name: str = Body("Candidate"),
    job_title: str = Body("Engineering Intern"),
):
    """Re-roll / regenerate a single interview question."""
    return await generator.regenerate_single_question(
        category=category,
        domain=domain,
        skill=skill,
        difficulty=difficulty,
        candidate_name=candidate_name,
        job_title=job_title,
    )


@router.post("/scorecard", response_model=Scorecard)
def submit_scorecard(scorecard: Scorecard):
    """Submit interview ratings and compute hiring score & recommendation."""
    if not scorecard.ratings:
        raise HTTPException(status_code=400, detail="Ratings cannot be empty")

    total_score = sum(r.score for r in scorecard.ratings)
    avg_score = round(total_score / len(scorecard.ratings), 2)
    scorecard.overall_score = avg_score

    # Determine recommendation
    if avg_score >= 4.5:
        scorecard.recommendation = "Strong Hire"
    elif avg_score >= 3.5:
        scorecard.recommendation = "Hire"
    elif avg_score >= 2.8:
        scorecard.recommendation = "Leaning Hire"
    elif avg_score >= 2.0:
        scorecard.recommendation = "Leaning No Hire"
    else:
        scorecard.recommendation = "No Hire"

    SCORECARDS_CACHE[scorecard.id] = scorecard
    return scorecard


@router.get("/export/{kit_id}")
def export_kit(kit_id: str, format: str = Query("markdown")):
    """Export interview kit in markdown, html, or json format."""
    if kit_id not in KITS_CACHE:
        raise HTTPException(status_code=404, detail="Interview kit not found")

    kit = KITS_CACHE[kit_id]
    fmt = format.lower().strip()

    if fmt == "markdown" or fmt == "md":
        content = KitExporter.to_markdown(kit)
        return PlainTextResponse(content, media_type="text/markdown")
    elif fmt == "html":
        content = KitExporter.to_html(kit)
        return HTMLResponse(content)
    elif fmt == "json":
        return Response(content=KitExporter.to_json(kit), media_type="application/json")
    else:
        raise HTTPException(status_code=400, detail="Supported formats: markdown, html, json")
