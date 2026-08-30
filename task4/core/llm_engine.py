import json
import os
import re
from typing import Dict, Any, List, Optional
import httpx
from core.models import (
    CandidateProfile,
    JobDescription,
    QuestionItem,
    RubricCriteria,
    SkillGapAnalysis,
)


SYSTEM_PROMPT = """You are a Senior Principal Technical Interviewer and University Recruiting Lead at a top-tier technology company.
Your role is to craft rigorous, fair, and calibrated interview questions specifically tailored for university INTERN and CO-OP candidates.

Rules for Intern Evaluation:
1. Calibrate for intern level: Focus on solid computer science fundamentals, learning agility, curiosity, intellectual honesty, and ability to reason through unfamiliar problems rather than 10 years of architectural experience.
2. Resume Deep Dives: Formulate specific questions testing actual personal contribution, design decisions, and trade-offs on the candidate's actual projects. Detect whether the candidate truly built the system or just followed a step-by-step tutorial.
3. Behavioral Questions: Use the STAR framework (Situation, Task, Action, Result) focused on realistic college/intern situations (coursework team dynamics, hackathons, deadline crunches, handling ambiguity, receiving critical feedback).
4. Clear Evaluation Rubrics: Provide explicit criteria for Poor (1-2), Good (3-4), and Excellent (5) responses.
5. Always return your response in valid JSON matching the requested schema.
"""


class BaseLLMEngine:
    async def generate_questions(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
        skill_analysis: SkillGapAnalysis,
        num_technical: int = 4,
        num_behavioral: int = 3,
        num_deep_dive: int = 2,
        num_scenario: int = 1,
        difficulty: str = "Standard Intern",
        focus_skills: Optional[List[str]] = None,
    ) -> List[QuestionItem]:
        raise NotImplementedError


class MockHeuristicEngine(BaseLLMEngine):
    """
    Intelligent local generator that crafts contextualized, bespoke questions
    from candidate resume details and job description requirements without requiring external API keys.
    """

    async def generate_questions(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
        skill_analysis: SkillGapAnalysis,
        num_technical: int = 4,
        num_behavioral: int = 3,
        num_deep_dive: int = 2,
        num_scenario: int = 1,
        difficulty: str = "Standard Intern",
        focus_skills: Optional[List[str]] = None,
    ) -> List[QuestionItem]:
        questions: List[QuestionItem] = []

        # 1. Generate Resume Deep Dive Questions
        if candidate.projects:
            for idx, proj in enumerate(candidate.projects[:num_deep_dive]):
                tech_stack = ", ".join(proj.technologies) if proj.technologies else "the stack"
                q_text = (
                    f"In your project '{proj.title}', you used {tech_stack}. "
                    f"Walk me through the architectural design of this system: what was the most difficult technical hurdle or edge case you encountered, "
                    f"what design trade-offs did you evaluate, and how did you verify your implementation?"
                )
                context = (
                    f"Directly probes candidate's hands-on contribution and technical ownership on '{proj.title}'. "
                    f"Verifies whether they independently reasoned about design decisions vs copy-pasting boilerplate."
                )
                key_points = [
                    f"Clear explanation of why {tech_stack} was chosen over alternatives.",
                    "Specific technical bottleneck (e.g., latency, state sync, database locks, component re-rendering) and systematic resolution.",
                    "Honest reflection on what they would improve or re-architect if building for 10x scale.",
                    f"Distinguishes personal contribution ({proj.role or 'developer'}) from pre-existing templates."
                ]
                probes = [
                    f"If you had to add end-to-end integration tests to '{proj.title}' today, what critical user flows would you test first?",
                    "What part of this project took the longest time to debug, and why?",
                    f"How did you manage state or data persistence across sessions in {proj.title}?"
                ]
                rubric = RubricCriteria(
                    poor=f"Cannot clearly explain the architecture of '{proj.title}', uses generic buzzwords, or reveals they only followed a basic tutorial without understanding.",
                    good=f"Explains the system flow and key decisions on '{proj.title}', describes a real bug or optimization, and articulates personal contribution clearly.",
                    excellent=f"Mastery over the codebase; articulates trade-offs, edge cases, failure recovery, and provides insightful retrospectives on scalability."
                )

                questions.append(
                    QuestionItem(
                        id=f"DD-PROJ-{idx+1:02d}",
                        category="Resume Deep Dive",
                        domain="Project Architecture & Ownership",
                        skills=proj.technologies if proj.technologies else ["Software Architecture"],
                        difficulty=difficulty if difficulty != "Mixed" else "Standard Intern",
                        question=q_text,
                        context=context,
                        expected_key_points=key_points,
                        follow_up_probes=probes,
                        rubric=rubric,
                        time_allocation_mins=7,
                        project_reference=proj.title,
                        is_custom_generated=True,
                    )
                )

        # 2. Generate Technical Questions tailored to Job Requirements + Candidate Overlap/Gaps
        target_skills = focus_skills if focus_skills else (skill_analysis.matched_skills + skill_analysis.missing_required_skills)
        if not target_skills:
            target_skills = ["JavaScript", "Python", "SQL", "REST API", "Git"]

        tech_templates = [
            {
                "skill_match": ["react", "frontend", "next.js", "javascript", "typescript"],
                "domain": "Frontend Architecture",
                "question": f"In modern frontend applications (such as with {job.title}), how do you design components for reusability, manage complex asynchronous data fetching, and handle loading/error states gracefully?",
                "context": f"Evaluates component lifecycle, state handling, and resilient UX patterns for {job.title}.",
                "key_points": [
                    "Separation of presentational and container/logic components.",
                    "Handling race conditions in asynchronous effects (cleanup/abort controllers).",
                    "Error boundaries and optimistic UI updates for delightful user experience.",
                    "Proper typing with TypeScript or structured prop contracts."
                ],
                "probes": [
                    "What happens if an API call completes after a component has unmounted?",
                    "How do you prevent prop drilling in multi-level component trees?"
                ],
                "rubric": RubricCriteria(
                    poor="Cannot explain how to handle async fetch errors or basic state lifecycle.",
                    good="Explains error boundaries, custom hooks, and clean state separation.",
                    excellent="Discusses AbortController, suspense boundaries, optimistic caching, and accessibility in loading states."
                )
            },
            {
                "skill_match": ["python", "fastapi", "backend", "api", "django", "node.js"],
                "domain": "Backend Systems & APIs",
                "question": f"When building an API endpoint for {job.title} that receives concurrent requests and writes to a database, how do you handle data validation, error handling, and ensure idempotency?",
                "context": "Assesses backend API design, schema validation, and concurrent transaction safety.",
                "key_points": [
                    "Input validation using schemas (e.g., Pydantic in FastAPI, Zod/Joi in Node).",
                    "Consistent structured HTTP error response envelopes and correct status codes.",
                    "Idempotency keys or unique constraint checks to prevent duplicate side effects.",
                    "Database transactions to guarantee atomicity."
                ],
                "probes": [
                    "How do you distinguish between 400 Bad Request, 422 Unprocessable Entity, and 500 Internal Error?",
                    "What happens if two concurrent requests try to update the same record simultaneously?"
                ],
                "rubric": RubricCriteria(
                    poor="Ignores data validation or returns 200 OK for validation failures.",
                    good="Defines schema validation, transactional boundaries, and proper HTTP status codes.",
                    excellent="Discusses optimistic vs pessimistic locking, idempotency tokens, and connection pool management."
                )
            },
            {
                "skill_match": ["sql", "postgresql", "database", "mysql", "mongodb"],
                "domain": "Database Design & Queries",
                "question": "How do you approach designing a normalized relational schema for a multi-entity feature, and how would you optimize a query that is slowing down under high data volume?",
                "context": "Tests relational modeling, indexing strategy, and query analysis skills.",
                "expected_key_points": [
                    "Normalization (1NF to 3NF) to reduce data redundancy and anomalies.",
                    "Foreign key constraints and index placement on frequently filtered/joined columns.",
                    "Using EXPLAIN ANALYZE to identify sequential scans and costly join operations.",
                    "Avoiding N+1 query patterns using eager loading or batching."
                ],
                "probes": [
                    "What is an N+1 query problem and how do you resolve it in an ORM?",
                    "When might you deliberately choose denormalization or a caching layer like Redis?"
                ],
                "rubric": RubricCriteria(
                    poor="Doesn't know what an index is or suggests querying the full table in memory.",
                    good="Explains foreign keys, B-tree indexes, and joins accurately.",
                    excellent="Deep understanding of execution plans, index selectivity, covering indexes, and N+1 ORM pitfalls."
                )
            },
            {
                "skill_match": ["pytorch", "machine learning", "deep learning", "nlp", "rag"],
                "domain": "Applied Machine Learning",
                "question": "When developing and deploying an ML model or RAG pipeline, how do you establish a rigorous validation baseline, and how do you evaluate model hallucinations or drift in production?",
                "context": "Evaluates scientific evaluation discipline and real-world ML lifecycle knowledge.",
                "expected_key_points": [
                    "Train/Validation/Test split with stratification or time-series awareness to prevent leakage.",
                    "Choosing domain-aligned metrics beyond raw accuracy (F1, Precision-Recall AUC, ROUGE/BLEU).",
                    "RAG evaluation metrics: Context Relevance, Groundedness/Faithfulness, and Answer Relevance.",
                    "Logging input distributions and monitoring for feature drift."
                ],
                "probes": [
                    "How do you detect when an LLM's response contradicts the retrieved context?",
                    "What strategies do you use when training data is severely imbalanced?"
                ],
                "rubric": RubricCriteria(
                    poor="Relies only on training accuracy or cannot define precision vs recall.",
                    good="Explains validation splits, metric trade-offs, and RAG retrieval evaluation.",
                    excellent="Discusses automated LLM-as-a-judge frameworks, embedding drift, and cost-latency-accuracy trade-offs."
                )
            },
            {
                "skill_match": ["docker", "kubernetes", "devops", "cloud", "aws", "terraform", "ci/cd"],
                "domain": "DevOps & Cloud Infrastructure",
                "question": "How do you structure a secure and reproducible container build and deployment pipeline for a cloud application, and how do you manage secrets across environments?",
                "context": "Assesses modern cloud deployment hygiene, container best practices, and security awareness.",
                "expected_key_points": [
                    "Multi-stage Dockerfiles to minimize final image footprint and eliminate build tools.",
                    "Non-root container user execution for security.",
                    "Injecting secrets via environment variables or secret managers (e.g., AWS Secrets Manager, Vault), never baking secrets into git or images.",
                    "Automated CI linting, testing, and container vulnerability scanning before release."
                ],
                "probes": [
                    "Why is `.dockerignore` essential in a build pipeline?",
                    "How do you ensure rollback capability if a new deployment crashes on launch?"
                ],
                "rubric": RubricCriteria(
                    poor="Suggests hardcoding API keys in Dockerfile or has no concept of environment variables.",
                    good="Explains multi-stage builds, CI runners, and secret masking.",
                    excellent="Details immutable infrastructure, least-privilege IAM, health/readiness probes, and canary rollouts."
                )
            }
        ]

        # Select relevant technical templates based on skills
        added_tech = 0
        for tmpl in tech_templates:
            if added_tech >= num_technical:
                break
            # Check if template matches any of target_skills
            if any(any(m in s.lower() for m in tmpl["skill_match"]) for s in target_skills):
                questions.append(
                    QuestionItem(
                        id=f"TECH-GEN-{added_tech+1:02d}",
                        category="Technical",
                        domain=tmpl["domain"],
                        skills=[s for s in target_skills if any(m in s.lower() for m in tmpl["skill_match"])][:4],
                        difficulty=difficulty if difficulty != "Mixed" else "Standard Intern",
                        question=tmpl["question"],
                        context=tmpl["context"],
                        expected_key_points=tmpl.get("key_points", tmpl.get("expected_key_points", [])),
                        follow_up_probes=tmpl["probes"],
                        rubric=tmpl["rubric"],
                        time_allocation_mins=5,
                        is_custom_generated=True,
                    )
                )
                added_tech += 1

        # Fallback technical question if we need more
        while added_tech < num_technical:
            questions.append(
                QuestionItem(
                    id=f"TECH-GEN-{added_tech+1:02d}",
                    category="Technical",
                    domain="System Fundamentals & Problem Solving",
                    skills=["Data Structures", "Algorithms", "Debugging"],
                    difficulty=difficulty if difficulty != "Mixed" else "Standard Intern",
                    question=f"For a core feature in {job.title}, how do you evaluate time and space complexity trade-offs when choosing between different data structures or algorithms?",
                    context=f"Assesses foundational CS problem-solving and efficiency analysis for {job.title}.",
                    expected_key_points=[
                        "Big-O time and auxiliary space complexity analysis.",
                        "Trade-offs between memory footprint and lookup velocity (e.g., Array vs HashMap vs Tree).",
                        "Practical considerations like cache locality and CPU branch prediction in high-throughput loops.",
                        "Writing clean, readable code before premature optimization."
                    ],
                    follow_up_probes=[
                        "Can you give an example where an O(n^2) algorithm might practically run faster than an O(n log n) algorithm for small n?",
                        "How do you profile memory allocations in your preferred language?"
                    ],
                    rubric=RubricCriteria(
                        poor="Cannot explain Big-O notation or confuses time and space complexity.",
                        good="Correctly analyzes complexity and explains standard data structure trade-offs.",
                        excellent="Articulates cache hierarchy effects, amortized analysis, and practical profiling tools."
                    ),
                    time_allocation_mins=5,
                    is_custom_generated=True,
                )
            )
            added_tech += 1

        # 3. Generate Behavioral STAR Questions calibrated for Interns
        behavioral_pool = [
            {
                "domain": "Learning Agility & Fast Ramp-Up",
                "question": f"At {job.company_overview.split('.')[0] if job.company_overview else 'our company'}, interns frequently encounter technologies they have never seen before. Describe a situation where you had to master a complex new framework or tool in less than two weeks for a project. What was your systematic learning strategy?",
                "context": "Assesses learning velocity, proactive documentation reading, and ramp-up independence.",
                "key_points": [
                    "Situation: Context of the deadline and unfamiliar technology.",
                    "Action: Strategic breakdown: documentation, small proof-of-concept prototypes, testing hypotheses.",
                    "Result: Successful delivery, reduced dependency on others, and lasting knowledge retention."
                ],
                "probes": [
                    "When you got stuck on a cryptic error, how long did you research before asking a peer or mentor for help?",
                    "How do you ensure you understand the core mechanics rather than just copying StackOverflow / AI snippets?"
                ],
                "rubric": RubricCriteria(
                    poor="Relies solely on trial-and-error without reading documentation, panics under time pressure.",
                    good="Shows structured learning method (docs -> toy examples -> implementation) and unblocks themselves.",
                    excellent="Synthesizes mental models, builds testable sandboxes, and documents findings for others."
                )
            },
            {
                "domain": "Collaboration & Conflict in Group Projects",
                "question": "Describe a project where you and a teammate had a fundamental disagreement about technical design, architecture, or task allocation. How did you handle the conversation and reach a resolution?",
                "context": "Tests emotional maturity, professional communication, and constructive technical debate.",
                "key_points": [
                    "Situation: Clear technical disagreement without personal attacks.",
                    "Action: Listened actively to peer's rationale, evaluated pros/cons objectively against project constraints, proposed an empirical test or compromise.",
                    "Result: Healthy team relationship preserved, project delivered successfully, agreed-on solution."
                ],
                "probes": [
                    "If your proposed approach was overruled by the team, how did you commit to the chosen path?",
                    "What did you learn about your own communication style from that experience?"
                ],
                "rubric": RubricCriteria(
                    poor="Shows bitterness, blames teammates, or aggressively insists on their own way without listening.",
                    good="Demonstrates active listening, objective criteria evaluation, and disagree-and-commit maturity.",
                    excellent="Facilitates constructive trade-off matrices, separates ego from ideas, and builds team consensus."
                )
            },
            {
                "domain": "Handling Ambiguity & Scope Scoping",
                "question": "Tell me about a time when you were given an open-ended project prompt with minimal technical specifications. How did you clarify requirements, define milestone scope, and deliver a working solution?",
                "context": "Assesses candidate's autonomy, scoping judgment, and bias for action.",
                "key_points": [
                    "Situation: Vague or unbounded requirements.",
                    "Action: Broke into Minimum Viable Product (MVP), formulated specific clarifying questions, created wireframes or architecture diagrams, validated assumptions early.",
                    "Result: Shipped functional product that satisfied stakeholder needs without gold-plating."
                ],
                "probes": [
                    "How did you prioritize which features were 'must-haves' vs 'nice-to-haves'?",
                    "How did you communicate progress along the way?"
                ],
                "rubric": RubricCriteria(
                    poor="Paralyzed by lack of explicit instructions, or spent weeks building the wrong thing without checking in.",
                    good="Defined MVP scope, asked targeted questions, and delivered iteratively.",
                    excellent="Demonstrates high agency, creates structured decision logs, proactively manages stakeholder expectations."
                )
            }
        ]

        for idx, b_item in enumerate(behavioral_pool[:num_behavioral]):
            questions.append(
                QuestionItem(
                    id=f"BEHAV-GEN-{idx+1:02d}",
                    category="Behavioral",
                    domain=b_item["domain"],
                    skills=["Communication", "Collaboration", "STAR Method", "Growth Mindset"],
                    difficulty="Foundational" if idx == 0 else "Standard Intern",
                    question=b_item["question"],
                    context=b_item["context"],
                    expected_key_points=b_item["key_points"],
                    follow_up_probes=b_item["probes"],
                    rubric=b_item["rubric"],
                    time_allocation_mins=5,
                    is_custom_generated=True,
                )
            )

        # 4. Generate Scenario / Live Problem Solving Question
        if num_scenario > 0:
            questions.append(
                QuestionItem(
                    id="SCEN-GEN-01",
                    category="Situational / Scenario",
                    domain="Production Troubleshooting & Communication",
                    skills=["Incident Management", "Communication", "Root Cause Analysis"],
                    difficulty="Standard Intern",
                    question=(
                        f"Scenario: You deployed your internship project feature to staging on a Thursday afternoon. "
                        f"Ten minutes later, an automated alert shows a sudden spike in 500 error rates and increased database latency. "
                        f"What exact steps do you take in the first 15 minutes to investigate and communicate?"
                    ),
                    context=f"Tests real-world production safety instincts, calm troubleshooting, and incident transparency for {job.title}.",
                    expected_key_points=[
                        "Immediate step: Alert your mentor/team in the engineering channel, do not try to secretly fix it.",
                        "Triage: Check if staging rollback is immediate to unblock other engineers.",
                        "Investigation: Inspect staging server error logs, recent commit diffs, and database query monitor.",
                        "Communication: Post updates with what is known, what is being tested, and root cause when found.",
                        "Follow-up: Write a regression test so this defect cannot recur."
                    ],
                    follow_up_probes=[
                        "What is the danger of pushing quick untested hotfixes directly to staging/production during an outage?",
                        "How do you write a constructive post-mortem note to share what happened with the team?"
                    ],
                    rubric=RubricCriteria(
                        poor="Hides the incident out of fear, or wildly makes random code edits without checking error logs.",
                        good="Communicates transparently with mentor, inspects logs systematically, and initiates safe rollback.",
                        excellent="Demonstrates calm incident command instincts, log correlation, safety-first rollback, and thorough root-cause retrospection."
                    ),
                    time_allocation_mins=6,
                    is_custom_generated=True,
                )
            )

        return questions


class OpenAIEngine(BaseLLMEngine):
    """Connects to OpenAI API (e.g. gpt-4o, gpt-3.5-turbo)."""

    def __init__(self, api_key: str, model_name: str = "gpt-4o"):
        self.api_key = api_key
        self.model_name = model_name or "gpt-4o"
        self.fallback = MockHeuristicEngine()

    async def generate_questions(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
        skill_analysis: SkillGapAnalysis,
        num_technical: int = 4,
        num_behavioral: int = 3,
        num_deep_dive: int = 2,
        num_scenario: int = 1,
        difficulty: str = "Standard Intern",
        focus_skills: Optional[List[str]] = None,
    ) -> List[QuestionItem]:
        if not self.api_key:
            return await self.fallback.generate_questions(
                candidate, job, skill_analysis, num_technical, num_behavioral, num_deep_dive, num_scenario, difficulty, focus_skills
            )

        prompt = f"""
Candidate Profile:
Name: {candidate.name}
Degree: {candidate.education.degree if candidate.education else 'N/A'} ({candidate.education.institution if candidate.education else ''})
Skills: {', '.join(candidate.get_all_skills_flat())}
Projects: {json.dumps([p.model_dump() for p in candidate.projects], indent=2)}

Job Description:
Title: {job.title}
Department: {job.department}
Required Skills: {', '.join(job.required_skills)}
Preferred Skills: {', '.join(job.preferred_skills)}
Responsibilities: {json.dumps(job.responsibilities)}

Skill Gap Analysis:
Matched: {', '.join(skill_analysis.matched_skills)}
Missing Required: {', '.join(skill_analysis.missing_required_skills)}
Target Difficulty: {difficulty}

Please generate an interview kit with:
- {num_deep_dive} Resume Deep Dive questions targeting the candidate's actual projects and design decisions.
- {num_technical} Technical questions calibrated for an intern matching the job tech stack and candidate skill overlaps.
- {num_behavioral} Behavioral (STAR method) questions calibrated for university/intern experience.
- {num_scenario} Situational/Scenario-based problem-solving question.

Return a JSON object with key 'questions' as an array of objects matching this schema:
[
  {{
    "id": "Q-01",
    "category": "Technical" | "Behavioral" | "Resume Deep Dive" | "Situational / Scenario",
    "domain": "string",
    "skills": ["string"],
    "difficulty": "{difficulty}",
    "question": "string",
    "context": "Why this question is selected for this candidate and job",
    "expected_key_points": ["point 1", "point 2", "point 3"],
    "follow_up_probes": ["probe 1", "probe 2"],
    "rubric": {{
      "poor": "Poor response description",
      "good": "Good response description",
      "excellent": "Excellent response description"
    }},
    "time_allocation_mins": 5,
    "project_reference": "Optional Project Title"
  }}
]
"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.7,
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    raw_qs = parsed.get("questions", parsed if isinstance(parsed, list) else [])
                    results = []
                    for item in raw_qs:
                        rubric_dict = item.get("rubric", {})
                        results.append(
                            QuestionItem(
                                id=item.get("id", f"Q-{len(results)+1:02d}"),
                                category=item.get("category", "Technical"),
                                domain=item.get("domain", "General Engineering"),
                                skills=item.get("skills", []),
                                difficulty=item.get("difficulty", difficulty),
                                question=item.get("question", ""),
                                context=item.get("context", ""),
                                expected_key_points=item.get("expected_key_points", []),
                                follow_up_probes=item.get("follow_up_probes", []),
                                rubric=RubricCriteria(
                                    poor=rubric_dict.get("poor", ""),
                                    good=rubric_dict.get("good", ""),
                                    excellent=rubric_dict.get("excellent", ""),
                                ),
                                time_allocation_mins=item.get("time_allocation_mins", 5),
                                project_reference=item.get("project_reference"),
                                is_custom_generated=True,
                            )
                        )
                    if results:
                        return results
        except Exception as e:
            print(f"OpenAI API call failed: {e}. Falling back to heuristic engine.")

        return await self.fallback.generate_questions(
            candidate, job, skill_analysis, num_technical, num_behavioral, num_deep_dive, num_scenario, difficulty, focus_skills
        )


class OllamaLLaMAEngine(BaseLLMEngine):
    """Connects to local or remote Ollama / LLaMA instance."""

    def __init__(self, endpoint_url: str = "http://localhost:11434", model_name: str = "llama3"):
        self.endpoint_url = endpoint_url.rstrip("/")
        self.model_name = model_name or "llama3"
        self.fallback = MockHeuristicEngine()

    async def generate_questions(
        self,
        candidate: CandidateProfile,
        job: JobDescription,
        skill_analysis: SkillGapAnalysis,
        num_technical: int = 4,
        num_behavioral: int = 3,
        num_deep_dive: int = 2,
        num_scenario: int = 1,
        difficulty: str = "Standard Intern",
        focus_skills: Optional[List[str]] = None,
    ) -> List[QuestionItem]:
        prompt = f"""
{SYSTEM_PROMPT}

Candidate: {candidate.name} ({candidate.education.degree if candidate.education else ''})
Skills: {', '.join(candidate.get_all_skills_flat())}
Projects: {json.dumps([p.title + ': ' + p.description for p in candidate.projects])}
Job: {job.title}
Required: {', '.join(job.required_skills)}
Target Difficulty: {difficulty}

Generate {num_deep_dive} Project Deep-Dive questions, {num_technical} Technical questions, {num_behavioral} Behavioral questions, and {num_scenario} Scenario question.
Output valid JSON only with format: {{"questions": [...]}}
"""
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(
                    f"{self.endpoint_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "format": "json",
                        "stream": False,
                    },
                )
                if resp.status_code == 200:
                    raw = resp.json().get("response", "")
                    parsed = json.loads(raw)
                    raw_qs = parsed.get("questions", parsed if isinstance(parsed, list) else [])
                    results = []
                    for item in raw_qs:
                        rubric_dict = item.get("rubric", {})
                        results.append(
                            QuestionItem(
                                id=item.get("id", f"Q-{len(results)+1:02d}"),
                                category=item.get("category", "Technical"),
                                domain=item.get("domain", "General Engineering"),
                                skills=item.get("skills", []),
                                difficulty=item.get("difficulty", difficulty),
                                question=item.get("question", ""),
                                context=item.get("context", ""),
                                expected_key_points=item.get("expected_key_points", []),
                                follow_up_probes=item.get("follow_up_probes", []),
                                rubric=RubricCriteria(
                                    poor=rubric_dict.get("poor", ""),
                                    good=rubric_dict.get("good", ""),
                                    excellent=rubric_dict.get("excellent", ""),
                                ),
                                time_allocation_mins=item.get("time_allocation_mins", 5),
                                project_reference=item.get("project_reference"),
                                is_custom_generated=True,
                            )
                        )
                    if results:
                        return results
        except Exception as e:
            print(f"Ollama/LLaMA call failed: {e}. Falling back to heuristic engine.")

        return await self.fallback.generate_questions(
            candidate, job, skill_analysis, num_technical, num_behavioral, num_deep_dive, num_scenario, difficulty, focus_skills
        )


def get_llm_engine(provider: str = "mock", api_key: Optional[str] = None, model_name: Optional[str] = None) -> BaseLLMEngine:
    """Factory method to get the selected LLM generator engine."""
    provider_clean = (provider or "mock").lower().strip()
    if provider_clean in ["openai", "gpt-4", "gpt-3.5", "gpt"]:
        return OpenAIEngine(api_key=api_key or os.getenv("OPENAI_API_KEY", ""), model_name=model_name or "gpt-4o")
    elif provider_clean in ["llama", "ollama", "local"]:
        return OllamaLLaMAEngine(model_name=model_name or "llama3")
    else:
        return MockHeuristicEngine()
