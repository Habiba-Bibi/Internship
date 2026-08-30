import argparse
import asyncio
import json
import os
import sys
from typing import Optional

# Ensure UTF-8 output on Windows terminals
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass


from core.models import (
    CandidateProfile,
    JobDescription,
    GenerationRequest,
)
from core.matcher import analyze_skill_gap
from core.question_bank import QuestionBank
from core.generator import InterviewQuestionGenerator
from core.exporter import KitExporter


def load_candidate_from_file(path: str) -> CandidateProfile:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return CandidateProfile.model_validate(data)


def load_job_from_file(path: str) -> JobDescription:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return JobDescription.model_validate(data)


async def run_generate(args):
    generator = InterviewQuestionGenerator()
    
    # Load candidate
    if os.path.exists(args.candidate):
        candidate = load_candidate_from_file(args.candidate)
    else:
        print(f"Candidate file not found: {args.candidate}")
        sys.exit(1)

    # Load job
    if os.path.exists(args.job):
        job = load_job_from_file(args.job)
    else:
        print(f"Job file not found: {args.job}")
        sys.exit(1)

    req = GenerationRequest(
        custom_candidate=candidate,
        custom_job=job,
        num_technical=args.technical,
        num_behavioral=args.behavioral,
        num_resume_deep_dive=args.deep_dive,
        num_scenario=args.scenario,
        difficulty=args.difficulty,
        llm_provider=args.provider,
        api_key=args.api_key,
        model_name=args.model,
    )

    print(f"🔄 Generating interview kit for {candidate.name} ({job.title})...")
    kit = await generator.generate_interview_kit(req)

    # Export
    output_fmt = args.format.lower()
    if output_fmt in ["markdown", "md"]:
        content = KitExporter.to_markdown(kit)
    elif output_fmt == "html":
        content = KitExporter.to_html(kit)
    elif output_fmt == "json":
        content = KitExporter.to_json(kit)
    else:
        content = KitExporter.to_markdown(kit)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Interview kit saved to: {args.output}")
    else:
        print("\n" + content)


def run_match(args):
    candidate = load_candidate_from_file(args.candidate)
    job = load_job_from_file(args.job)
    analysis = analyze_skill_gap(candidate, job)

    print(f"\n=======================================================")
    print(f"📊 SKILL GAP ANALYSIS: {candidate.name} -> {job.title}")
    print(f"=======================================================")
    print(f"Match Score: {analysis.match_score_percentage}%\n")
    print(f"✅ Matched Skills: {', '.join(analysis.matched_skills)}")
    print(f"⚠️  Missing Required Skills: {', '.join(analysis.missing_required_skills) if analysis.missing_required_skills else 'None'}")
    print(f"💡 Missing Preferred Skills: {', '.join(analysis.missing_preferred_skills) if analysis.missing_preferred_skills else 'None'}")
    print(f"⭐ Bonus Strengths: {', '.join(analysis.candidate_unique_strengths)}")
    print("\n🎯 Recommended Focus Areas:")
    for idx, fa in enumerate(analysis.recommended_focus_areas, 1):
        print(f"  {idx}. {fa}")
    print(f"=======================================================\n")


def run_bank(args):
    bank = QuestionBank()
    results = bank.filter(
        category=args.category,
        domain=args.domain,
        skill=args.skill,
        difficulty=args.difficulty,
        search_query=args.query,
    )
    print(f"\n📚 Question Bank ({len(results)} matches):")
    for q in results:
        print(f"\n[{q.id}] [{q.category}] [{q.difficulty}] {q.question}")
        print(f"  Domain: {q.domain} | Skills: {', '.join(q.skills)}")
        print(f"  Time: {q.time_allocation_mins} mins")


def run_list(args):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cand_dir = os.path.join(base_dir, "data", "candidates")
    job_dir = os.path.join(base_dir, "data", "jobs")

    print("\n👤 Available Candidates:")
    if os.path.exists(cand_dir):
        for f in os.listdir(cand_dir):
            if f.endswith(".json"):
                cand = load_candidate_from_file(os.path.join(cand_dir, f))
                print(f"  - [{cand.id}] {cand.name} ({cand.target_role}) -> data/candidates/{f}")

    print("\n💼 Available Job Descriptions:")
    if os.path.exists(job_dir):
        for f in os.listdir(job_dir):
            if f.endswith(".json"):
                job = load_job_from_file(os.path.join(job_dir, f))
                print(f"  - [{job.id}] {job.title} ({job.department}) -> data/jobs/{f}")
    print("")


def main():
    parser = argparse.ArgumentParser(description="Intern Interview Question Generator CLI")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate an interview kit")
    gen_parser.add_argument("--candidate", "-c", required=True, help="Path to candidate profile JSON")
    gen_parser.add_argument("--job", "-j", required=True, help="Path to job description JSON")
    gen_parser.add_argument("--output", "-o", help="Output file path (e.g. kit.md, kit.html, kit.json)")
    gen_parser.add_argument("--format", "-f", default="markdown", choices=["markdown", "html", "json"], help="Output format")
    gen_parser.add_argument("--technical", "-t", type=int, default=4, help="Number of technical questions")
    gen_parser.add_argument("--behavioral", "-b", type=int, default=3, help="Number of behavioral questions")
    gen_parser.add_argument("--deep-dive", "-d", type=int, default=2, help="Number of resume deep-dive questions")
    gen_parser.add_argument("--scenario", "-s", type=int, default=1, help="Number of scenario questions")
    gen_parser.add_argument("--difficulty", default="Standard Intern", choices=["Foundational", "Standard Intern", "Advanced Intern", "Mixed"])
    gen_parser.add_argument("--provider", default="mock", choices=["mock", "openai", "llama"], help="LLM Provider")
    gen_parser.add_argument("--api-key", help="API key if using OpenAI or cloud provider")
    gen_parser.add_argument("--model", help="Model name (e.g. gpt-4o, llama3)")

    # match command
    match_parser = subparsers.add_parser("match", help="Perform skill-gap analysis")
    match_parser.add_argument("--candidate", "-c", required=True, help="Path to candidate profile JSON")
    match_parser.add_argument("--job", "-j", required=True, help="Path to job description JSON")

    # bank command
    bank_parser = subparsers.add_parser("bank", help="Search the question bank")
    bank_parser.add_argument("--category", help="Filter by category")
    bank_parser.add_argument("--domain", help="Filter by domain")
    bank_parser.add_argument("--skill", help="Filter by skill")
    bank_parser.add_argument("--difficulty", help="Filter by difficulty")
    bank_parser.add_argument("--query", "-q", help="Search query string")

    # list command
    subparsers.add_parser("list", help="List available sample candidates and jobs")

    args = parser.parse_args()

    if args.command == "generate":
        asyncio.run(run_generate(args))
    elif args.command == "match":
        run_match(args)
    elif args.command == "bank":
        run_bank(args)
    elif args.command == "list":
        run_list(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
