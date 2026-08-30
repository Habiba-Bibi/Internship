import uuid
import datetime
from typing import Optional, List, Dict
from core.models import (
    CandidateProfile,
    JobDescription,
    InterviewKit,
    InterviewSection,
    QuestionItem,
    GenerationRequest,
    Education,
    ProjectItem,
    ExperienceItem,
    RubricCriteria,
)
from core.matcher import analyze_skill_gap, extract_skills_from_text
from core.question_bank import QuestionBank
from core.llm_engine import get_llm_engine


class InterviewQuestionGenerator:
    """Main pipeline orchestrator for generating customized intern interview kits."""

    def __init__(self, question_bank: Optional[QuestionBank] = None):
        self.question_bank = question_bank or QuestionBank()

    def parse_raw_resume_to_candidate(self, text: str, name: str = "Candidate") -> CandidateProfile:
        """Parse unformatted plain resume text into a CandidateProfile model."""
        extracted_skills = extract_skills_from_text(text)
        
        # Simple heuristic lines extraction for projects / experience
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        projects = []
        experience = []
        
        # Default placeholder project if none explicitly structured
        if lines:
            projects.append(
                ProjectItem(
                    title="Portfolio / Featured Project",
                    description=text[:400] + ("..." if len(text) > 400 else ""),
                    technologies=extracted_skills[:5],
                )
            )
        
        return CandidateProfile(
            id=f"cand_raw_{uuid.uuid4().hex[:6]}",
            name=name,
            education=Education(degree="Computer Science / Related Field"),
            skills={"extracted": extracted_skills},
            skill_levels={s: "Intermediate" for s in extracted_skills[:6]},
            projects=projects,
            experience=experience,
            raw_resume_text=text,
        )

    def parse_raw_job_to_description(self, text: str, title: str = "Software Engineering Intern") -> JobDescription:
        """Parse raw job description text into a JobDescription model."""
        extracted_skills = extract_skills_from_text(text)
        reqs = [f"Hands-on proficiency with {s}" for s in extracted_skills[:4]]
        prefs = [f"Familiarity with {s}" for s in extracted_skills[4:8]]
        
        return JobDescription(
            id=f"job_raw_{uuid.uuid4().hex[:6]}",
            title=title,
            department="Engineering",
            responsibilities=[text[:250] + "..."],
            required_skills=reqs if reqs else ["Strong programming fundamentals (Python, JavaScript, or C++)"],
            preferred_skills=prefs,
            raw_job_text=text,
        )

    async def generate_interview_kit(self, request: GenerationRequest) -> InterviewKit:
        """
        Generate a complete, structured interview kit for the candidate and job.
        Combines skill-gap analysis, RAG retrieval from the question bank, and LLM generation.
        """
        # 1. Resolve Candidate Profile
        candidate: CandidateProfile
        if request.custom_candidate:
            candidate = request.custom_candidate
        elif request.raw_resume_text:
            candidate = self.parse_raw_resume_to_candidate(request.raw_resume_text)
        else:
            raise ValueError("No candidate profile or resume provided.")

        # 2. Resolve Job Description
        job: JobDescription
        if request.custom_job:
            job = request.custom_job
        elif request.raw_job_text:
            job = self.parse_raw_job_to_description(request.raw_job_text)
        else:
            raise ValueError("No job description provided.")

        # 3. Perform Skill Gap & Alignment Analysis
        skill_analysis = analyze_skill_gap(candidate, job)

        # 4. Generate dynamic questions using the selected LLM engine
        llm = get_llm_engine(
            provider=request.llm_provider,
            api_key=request.api_key,
            model_name=request.model_name,
        )

        generated_questions = await llm.generate_questions(
            candidate=candidate,
            job=job,
            skill_analysis=skill_analysis,
            num_technical=request.num_technical,
            num_behavioral=request.num_behavioral,
            num_deep_dive=request.num_resume_deep_dive,
            num_scenario=request.num_scenario,
            difficulty=request.difficulty,
            focus_skills=request.focus_skills,
        )

        # 5. Retrieve supplemental high-yield questions from the curated bank if needed
        # (e.g. if generated questions were fewer than requested)
        existing_bank_qs = []
        if len(generated_questions) < (request.num_technical + request.num_behavioral + request.num_resume_deep_dive):
            needed_tech = max(0, request.num_technical - sum(1 for q in generated_questions if q.category == "Technical"))
            if needed_tech > 0:
                bank_tech = self.question_bank.find_relevant_questions(
                    target_skills=skill_analysis.matched_skills + job.required_skills,
                    category="Technical",
                    difficulty=request.difficulty,
                    limit=needed_tech,
                )
                existing_bank_qs.extend(bank_tech)

        all_questions = generated_questions + existing_bank_qs

        # 6. Organize into structured Interview Sections with time allocations
        sections: List[InterviewSection] = []

        # Section 1: Introduction & Candidate Background (5 mins)
        intro_q = QuestionItem(
            id="INTRO-01",
            category="Introduction",
            domain="Overview",
            skills=["Communication", "Self-Presentation"],
            difficulty="Foundational",
            question=f"Welcome {candidate.name}! To start, tell me about your background, what motivated you to apply for the {job.title} role, and what you're most excited to learn during an internship.",
            context="Icebreaker to build rapport, evaluate communication clarity, and gauge intrinsic motivation.",
            expected_key_points=[
                "Concise 2-minute elevator pitch connecting academic background to engineering interests.",
                f"Articulates why this specific role ({job.title}) and team align with career goals.",
                "Enthusiasm for mentorship and rapid learning."
            ],
            follow_up_probes=[
                "What has been your favorite computer science course so far and why?"
            ],
            rubric=RubricCriteria(
                poor="Unprepared, unfocused rambling, or expresses zero knowledge of the company/role.",
                good="Clear, articulate summary of background and clear enthusiasm for the internship.",
                excellent="Compelling narrative connecting coursework/projects directly to the role's mission."
            ),
            time_allocation_mins=5,
        )
        sections.append(
            InterviewSection(
                title="Part 1: Introduction & Motivation",
                duration_mins=5,
                description="Welcome, mutual introductions, and candidate career interests.",
                questions=[intro_q],
            )
        )

        # Section 2: Resume & Project Deep Dive (10-15 mins)
        deep_dive_qs = [q for q in all_questions if q.category == "Resume Deep Dive"]
        if deep_dive_qs:
            sections.append(
                InterviewSection(
                    title="Part 2: Resume & Project Architecture Deep-Dive",
                    duration_mins=sum(q.time_allocation_mins for q in deep_dive_qs),
                    description="Probing candidate's actual projects, technical ownership, design choices, and real contributions.",
                    questions=deep_dive_qs,
                )
            )

        # Section 3: Technical Fundamentals & Role Alignment (15-20 mins)
        tech_qs = [q for q in all_questions if q.category == "Technical"]
        if tech_qs:
            sections.append(
                InterviewSection(
                    title="Part 3: Technical Concepts & Problem Solving",
                    duration_mins=sum(q.time_allocation_mins for q in tech_qs),
                    description=f"Core technical competency evaluation aligned with {job.title} requirements.",
                    questions=tech_qs,
                )
            )

        # Section 4: Behavioral & STAR Competencies (10 mins)
        behav_qs = [q for q in all_questions if q.category == "Behavioral"]
        if behav_qs:
            sections.append(
                InterviewSection(
                    title="Part 4: Behavioral & Culture Alignment (STAR)",
                    duration_mins=sum(q.time_allocation_mins for q in behav_qs),
                    description="Assessing learning agility, handling ambiguity, team collaboration, and receiving feedback.",
                    questions=behav_qs,
                )
            )

        # Section 5: Scenario / Live Problem Solving (if requested) (5-10 mins)
        scen_qs = [q for q in all_questions if q.category == "Situational / Scenario"]
        if scen_qs:
            sections.append(
                InterviewSection(
                    title="Part 5: Situational & Practical Engineering Scenario",
                    duration_mins=sum(q.time_allocation_mins for q in scen_qs),
                    description="Evaluating pragmatic decision-making, incident response, and team communication.",
                    questions=scen_qs,
                )
            )

        # Section 6: Candidate Q&A & Next Steps (5 mins)
        wrap_q = QuestionItem(
            id="WRAP-01",
            category="Debrief",
            domain="Candidate Q&A",
            skills=["Curiosity", "Engagement"],
            difficulty="Foundational",
            question="What questions do you have for me about our team culture, daily engineering workflows, or the internship program?",
            context="Allows the candidate to interview the company; high-signal indicator of intellectual curiosity.",
            expected_key_points=[
                "Candidate asks 2-3 thoughtful questions about team dynamics, mentorship, tech stack, or roadmap.",
                "Shows genuine curiosity about what a typical day looks like for an intern."
            ],
            follow_up_probes=[
                "Are there specific areas of the stack you hope to touch in your first month?"
            ],
            rubric=RubricCriteria(
                poor="Has zero questions or only asks when the interview will end.",
                good="Asks standard questions about team size, tech stack, and typical day.",
                excellent="Asks thoughtful questions about mentorship structure, release cycles, or technical challenges."
            ),
            time_allocation_mins=5,
        )
        sections.append(
            InterviewSection(
                title="Part 6: Candidate Q&A & Debrief",
                duration_mins=5,
                description="Open floor for candidate to ask questions about the team, culture, and roadmap.",
                questions=[wrap_q],
            )
        )

        total_duration = sum(s.duration_mins for s in sections)

        notes_template = (
            f"--- INTERVIEWER NOTES & EVALUATION SUMMARY ---\n"
            f"Candidate: {candidate.name}\n"
            f"Target Role: {job.title}\n"
            f"Date: {datetime.datetime.now().strftime('%Y-%m-%d')}\n"
            f"Overall Skill Match: {skill_analysis.match_score_percentage}%\n\n"
            f"Strengths Observed:\n"
            f"- \n\n"
            f"Areas of Concern / Follow-up Needed:\n"
            f"- \n\n"
            f"Hiring Recommendation: [ ] Strong Hire  [ ] Hire  [ ] Leaning Hire  [ ] No Hire\n"
        )

        flat_questions = [intro_q] + all_questions + [wrap_q]

        return InterviewKit(
            id=f"kit_{uuid.uuid4().hex[:8]}",
            candidate_id=candidate.id,
            candidate_name=candidate.name,
            job_id=job.id,
            job_title=job.title,
            generated_at=datetime.datetime.now().isoformat(),
            total_duration_mins=total_duration,
            target_level=job.level,
            skill_analysis=skill_analysis,
            sections=sections,
            questions=flat_questions,
            interviewer_notes_template=notes_template,
        )

    async def regenerate_single_question(
        self,
        category: str,
        domain: str,
        skill: str,
        difficulty: str,
        candidate_name: str = "Candidate",
        job_title: str = "Engineering Intern",
    ) -> QuestionItem:
        """Regenerate or roll an alternative question for a specific category/skill."""
        # Check bank first
        bank_matches = self.question_bank.filter(category=category, skill=skill, difficulty=difficulty)
        if bank_matches:
            import random
            selected = random.choice(bank_matches)
            # Create a clone with unique ID
            return QuestionItem(
                id=f"Q-REGEN-{uuid.uuid4().hex[:4].upper()}",
                category=selected.category,
                domain=selected.domain,
                skills=selected.skills,
                difficulty=selected.difficulty,
                question=selected.question,
                context=selected.context,
                expected_key_points=selected.expected_key_points,
                follow_up_probes=selected.follow_up_probes,
                rubric=selected.rubric,
                time_allocation_mins=selected.time_allocation_mins,
                is_custom_generated=True,
            )

        # Heuristic generation for requested skill
        return QuestionItem(
            id=f"Q-REGEN-{uuid.uuid4().hex[:4].upper()}",
            category=category,
            domain=domain or "Core Engineering",
            skills=[skill] if skill else ["Problem Solving"],
            difficulty=difficulty or "Standard Intern",
            question=f"In the context of {job_title}, how would you approach solving a technical challenge involving {skill or 'core architecture'}, and what edge cases would you test for?",
            context=f"Targeted inquiry for {skill} competency.",
            expected_key_points=[
                f"Clear understanding of {skill} principles and best practices.",
                "Identification of standard edge cases (null inputs, latency, concurrency).",
                "Structured explanation of testing and validation strategy."
            ],
            follow_up_probes=[
                f"What is the most common mistake beginners make with {skill}?",
                "How does this scale when data volume grows?"
            ],
            rubric=RubricCriteria(
                poor=f"Cannot articulate fundamentals of {skill}.",
                good=f"Explains {skill} accurately with sensible design decisions.",
                excellent=f"Demonstrates deep nuance, edge-case mitigation, and production experience with {skill}."
            ),
            time_allocation_mins=5,
            is_custom_generated=True,
        )
