import re
from typing import List, Dict, Set, Tuple
from core.models import CandidateProfile, JobDescription, SkillGapAnalysis


# Known tech skills and synonyms mapping for intelligent semantic normalization
SKILL_SYNONYMS: Dict[str, str] = {
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ts": "TypeScript",
    "typescript": "TypeScript",
    "py": "Python",
    "python": "Python",
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "next": "Next.js",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "express": "Express",
    "express.js": "Express",
    "fastapi": "FastAPI",
    "django": "Django",
    "flask": "Flask",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "sql": "SQL",
    "mysql": "MySQL",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",
    "redis": "Redis",
    "docker": "Docker",
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "terraform": "Terraform",
    "aws": "AWS",
    "git": "Git",
    "github": "Git",
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "tensorflow": "TensorFlow",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "huggingface": "Hugging Face",
    "hugging face": "Hugging Face",
    "transformers": "Transformers",
    "html": "HTML",
    "html5": "HTML",
    "css": "CSS",
    "css3": "CSS",
    "sass": "Sass",
    "tailwind": "TailwindCSS",
    "tailwindcss": "TailwindCSS",
    "graphql": "GraphQL",
    "rest": "REST API",
    "restful": "REST API",
    "jest": "Jest",
    "pytest": "Pytest",
    "ci/cd": "CI/CD",
    "golang": "Go",
    "go": "Go",
    "c++": "C++",
    "cpp": "C++",
    "bash": "Bash",
    "shell": "Bash",
    "rag": "RAG",
    "vector database": "Vector Databases",
    "chroma": "ChromaDB",
    "chromadb": "ChromaDB",
    "faiss": "FAISS",
    "celery": "Celery",
    "rabbitmq": "RabbitMQ",
}


def normalize_skill(skill_str: str) -> str:
    """Normalize skill name using standard casing and synonym resolution."""
    cleaned = skill_str.strip().lower()
    # Remove parenthetical notes e.g. "JavaScript (ES6+)" -> "javascript"
    cleaned = re.sub(r"\(.*?\)", "", cleaned).strip()
    return SKILL_SYNONYMS.get(cleaned, skill_str.strip())


def extract_skills_from_text(text: str) -> List[str]:
    """Extract known technical skills from raw text description."""
    if not text:
        return []
    found = []
    text_lower = text.lower()
    for raw_key, canonical in SKILL_SYNONYMS.items():
        pattern = r"\b" + re.escape(raw_key) + r"\b"
        if re.search(pattern, text_lower):
            if canonical not in found:
                found.append(canonical)
    return found


def analyze_skill_gap(
    candidate: CandidateProfile, job: JobDescription
) -> SkillGapAnalysis:
    """
    Perform a comprehensive skill-gap analysis between an intern profile
    and a target job description.
    """
    # 1. Gather all candidate skills
    candidate_skills_raw = candidate.get_all_skills_flat()
    candidate_skills_norm: Dict[str, str] = {}  # norm_lower -> display_name
    for s in candidate_skills_raw:
        norm = normalize_skill(s)
        candidate_skills_norm[norm.lower()] = norm

    # Also scan candidate resume text / projects for implicit skills
    for p in candidate.projects:
        for s in extract_skills_from_text(f"{p.title} {p.description}"):
            norm = normalize_skill(s)
            candidate_skills_norm[norm.lower()] = norm

    if candidate.raw_resume_text:
        for s in extract_skills_from_text(candidate.raw_resume_text):
            norm = normalize_skill(s)
            candidate_skills_norm[norm.lower()] = norm

    # 2. Extract and normalize Job Required Skills
    job_required_skills: List[str] = []
    for req in job.required_skills:
        extracted = extract_skills_from_text(req)
        if extracted:
            job_required_skills.extend(extracted)
        else:
            job_required_skills.append(normalize_skill(req))

    # 3. Extract and normalize Job Preferred Skills
    job_pref_skills: List[str] = []
    for pref in job.preferred_skills:
        extracted = extract_skills_from_text(pref)
        if extracted:
            job_pref_skills.extend(extracted)
        else:
            job_pref_skills.append(normalize_skill(pref))

    # Deduplicate
    job_required_skills = list(dict.fromkeys(job_required_skills))
    job_pref_skills = list(dict.fromkeys(job_pref_skills))

    matched: List[str] = []
    missing_req: List[str] = []
    missing_pref: List[str] = []

    # Check Required Skills
    for req in job_required_skills:
        req_norm = normalize_skill(req)
        if req_norm.lower() in candidate_skills_norm or any(
            req_norm.lower() in s.lower() for s in candidate_skills_norm.keys()
        ):
            matched.append(req_norm)
        else:
            missing_req.append(req_norm)

    # Check Preferred Skills
    for pref in job_pref_skills:
        pref_norm = normalize_skill(pref)
        if pref_norm.lower() in candidate_skills_norm or any(
            pref_norm.lower() in s.lower() for s in candidate_skills_norm.keys()
        ):
            if pref_norm not in matched:
                matched.append(pref_norm)
        else:
            if pref_norm not in missing_req:
                missing_pref.append(pref_norm)

    # Deduplicate matched
    matched = list(dict.fromkeys(matched))

    # Calculate candidate unique strengths (skills the candidate has that aren't specifically requested)
    unique_strengths = []
    all_job_skills_lower = {
        s.lower() for s in job_required_skills + job_pref_skills
    }
    for norm_lower, display in candidate_skills_norm.items():
        if norm_lower not in all_job_skills_lower and not any(
            norm_lower in js for js in all_job_skills_lower
        ):
            unique_strengths.append(display)

    # Compute match percentage score
    total_req = len(job_required_skills)
    total_pref = len(job_pref_skills)
    total_weight = (total_req * 1.5) + (total_pref * 0.75)

    req_matched_count = sum(
        1
        for s in job_required_skills
        if normalize_skill(s).lower() in [m.lower() for m in matched]
    )
    pref_matched_count = sum(
        1
        for s in job_pref_skills
        if normalize_skill(s).lower() in [m.lower() for m in matched]
    )

    if total_weight > 0:
        matched_weight = (req_matched_count * 1.5) + (
            pref_matched_count * 0.75
        )
        match_score = round(min(100.0, (matched_weight / total_weight) * 100), 1)
    else:
        match_score = 80.0

    # Recommended focus areas for interview
    focus_areas = []
    if missing_req:
        focus_areas.append(
            f"Assess foundational transferrable knowledge for missing requirements: {', '.join(missing_req[:3])}"
        )
    if candidate.projects:
        top_proj = candidate.projects[0]
        focus_areas.append(
            f"Deep-dive into '{top_proj.title}' to evaluate real technical ownership vs tutorial following"
        )
    if matched:
        focus_areas.append(
            f"Verify depth of core matched strengths: {', '.join(matched[:3])}"
        )
    focus_areas.append(
        "Evaluate learning agility, collaboration in university/team settings, and code quality instincts"
    )

    return SkillGapAnalysis(
        matched_skills=matched,
        missing_required_skills=missing_req,
        missing_preferred_skills=missing_pref,
        candidate_unique_strengths=unique_strengths[:6],
        match_score_percentage=match_score,
        recommended_focus_areas=focus_areas,
    )
