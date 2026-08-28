#!/usr/bin/env python3
"""
Internship AI Recommendation & Learning Roadmap CLI
===================================================
Command-line and interactive interface to:
1. Predict best-fit courses via Collaborative Filtering (Matrix Factorization SVD).
2. Generate step-by-step learning roadmaps (Beginner -> Intermediate -> Advanced).
3. Handle brand-new students with zero history via Cold-Start scoring.
4. Export roadmaps to Markdown or JSON.
"""

import sys
import json
import argparse
from pathlib import Path
from recommender import InternshipRecommender

# Ensure stdout handles UTF-8 on Windows cp1252 consoles without error
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AVAILABLE_FIELDS = [
    "Web & Full-Stack Development",
    "Data Science & Artificial Intelligence",
    "Cloud Computing & DevOps",
    "Cybersecurity & Network Security",
    "Mobile App Development",
    "UI/UX & Product Design",
]


def print_banner():
    print("=" * 80)
    print("      >> AI INTERNSHIP COURSE RECOMMENDER & ROADMAP GENERATOR <<      ")
    print("   Collaborative Filtering | Cold-Start Engine | Topological Level Scheduler   ")
    print("=" * 80)


def print_roadmap_table(result: dict):
    """Pretty-print a structured step-by-step roadmap."""
    mode = result.get("mode")
    roadmap = result["roadmap"]
    
    print("\n" + "-" * 80)
    if mode == "existing_intern":
        print(f"[+] INTERN PROFILE: {result['intern_name']} (ID: {result['intern_id']})")
        print(f"    Career Track:  {result['career_field']}")
        print(f"    Education:     {result['education_level']} in {result['academic_major']}")
        print(f"    Completed:     {result['past_courses_completed_count']} courses in history")
    else:
        print(f"[+] NEW INTERN (Cold-Start): {result['intern_name']}")
        print(f"    Target Track:  {result['career_field']}")
        print(f"    Background:    {result['education_level']} | Major: {result['academic_major']}")
        print(f"    History:       0 prior enrollments (Cold-Start Prior Applied)")

    print(f"\n[i] ROADMAP OVERVIEW:")
    print(f"    - Recommended Courses: {roadmap['total_courses']} modules")
    print(f"    - Estimated Duration:  {roadmap['total_estimated_weeks']} weeks (~{roadmap['total_estimated_weeks']/4:.1f} months)")
    print(f"    - Total Academic Credits: {roadmap['total_credit_units']} credits")
    if roadmap.get("injected_prerequisites_count", 0) > 0:
        print(f"    - [!] Auto-Injected Prerequisites: {roadmap['injected_prerequisites_count']} foundational requirement(s)")
    print("-" * 80)

    for phase in roadmap["phases"]:
        print(f"\n>>> {phase['phase_title'].upper()} ({phase['difficulty_level'].upper()})")
        print(f"    Description: {phase['phase_description']}")
        print(f"    Total Duration: {phase['total_weeks']} weeks | Credits: {phase['total_credits']}")
        print("    " + "-" * 74)

        for step in phase["steps"]:
            step_num = step["step_number"]
            cid = step["course_id"]
            title = step["course_title"]
            rating = step["predicted_rating"]
            weeks = step["duration_weeks"]
            credits = step["credit_units"]
            field = step["career_field"]
            reason = step["recommendation_reason"]
            prereq = step["prerequisite_course_id"]
            is_injected = step.get("is_injected_prereq", False)

            injected_tag = " [!] AUTO-ADDED PREREQUISITE" if is_injected else ""
            print(f"\n    Step {step_num:02d}: [{cid}] {title}{injected_tag}")
            print(f"            Predicted Affinity: {rating} / 5.0  |  Duration: {weeks} wks  |  Credits: {credits}  |  Field: {field}")
            if prereq:
                print(f"            Prerequisite: [{prereq}] {step['prerequisite_course_title']} (Satisfied)")
            print(f"            Why recommended: {reason}")
            print(f"            Summary: {step['description']}")

    print("\n" + "=" * 80)
    print("[V] ROADMAP INTEGRITY: No difficult courses assigned before their foundational basics!")
    print("=" * 80 + "\n")


def export_to_markdown(result: dict, filepath: Path):
    """Export the roadmap to a clean Markdown file."""
    roadmap = result["roadmap"]
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Personalized Learning Roadmap: {result['intern_name']}\n\n")
        f.write(f"- **Student Status:** {'Existing Intern (' + result.get('intern_id', '') + ')' if result['mode'] == 'existing_intern' else 'New Student (Cold-Start)'}\n")
        f.write(f"- **Target Career Track:** {result['career_field']}\n")
        f.write(f"- **Education Level:** {result['education_level']} ({result['academic_major']})\n")
        f.write(f"- **Total Modules:** {roadmap['total_courses']} courses\n")
        f.write(f"- **Total Duration:** {roadmap['total_estimated_weeks']} weeks\n")
        f.write(f"- **Total Credits:** {roadmap['total_credit_units']} credits\n\n")

        for phase in roadmap["phases"]:
            f.write(f"## {phase['phase_badge']} {phase['phase_title']}\n\n")
            f.write(f"*{phase['phase_description']}*\n\n")
            f.write(f"**Phase Duration:** {phase['total_weeks']} weeks | **Credits:** {phase['total_credits']}\n\n")
            f.write("| Step | Code | Course Title | Weeks | Credits | Predicted Rating | Reason |\n")
            f.write("| :---: | :---: | :--- | :---: | :---: | :---: | :--- |\n")
            for step in phase["steps"]:
                f.write(f"| {step['step_number']} | `{step['course_id']}` | **{step['course_title']}** | {step['duration_weeks']} | {step['credit_units']} | {step['predicted_rating']} ★ | {step['recommendation_reason']} |\n")
            f.write("\n")

    print(f"✅ Successfully exported Markdown roadmap to: {filepath}")


def interactive_mode(engine: InternshipRecommender):
    """Interactive CLI guide for users."""
    print_banner()
    print("Welcome! Please select an option:")
    print("  1. Generate roadmap for an existing intern profile")
    print("  2. Generate roadmap for a brand-new student (Cold-Start)")
    print("  3. Train and evaluate Collaborative Filtering Model (RMSE/MAE)")
    print("  4. Exit")

    choice = input("\nEnter choice (1-4): ").strip()

    if choice == "1":
        intern_id = input("Enter Intern ID (e.g. INT-0001 to INT-0600) [Default INT-0001]: ").strip()
        if not intern_id:
            intern_id = "INT-0001"
        try:
            res = engine.recommend_for_intern(intern_id=intern_id)
            print_roadmap_table(res)
            exp = input("Would you like to export this to a Markdown file? (y/n): ").strip().lower()
            if exp == "y":
                out_path = Path(f"roadmap_{intern_id}.md")
                export_to_markdown(res, out_path)
        except Exception as e:
            print(f"❌ Error: {e}")

    elif choice == "2":
        name = input("Enter Student Full Name [Default: Alex Rivera]: ").strip() or "Alex Rivera"
        print("\nAvailable Career Fields:")
        for idx, field in enumerate(AVAILABLE_FIELDS, 1):
            print(f"  {idx}. {field}")
        field_idx = input("Select Career Field (1-6) [Default: 2]: ").strip() or "2"
        try:
            field_name = AVAILABLE_FIELDS[int(field_idx) - 1]
        except (ValueError, IndexError):
            field_name = AVAILABLE_FIELDS[1]

        edu = input("Education Level [Default: Undergraduate Student]: ").strip() or "Undergraduate Student"
        major = input("Academic Major [Default: Computer Science]: ").strip() or "Computer Science"

        res = engine.recommend_for_new_student(
            student_name=name,
            target_career_field=field_name,
            education_level=edu,
            academic_major=major,
        )
        print_roadmap_table(res)
        exp = input("Would you like to export this to a Markdown file? (y/n): ").strip().lower()
        if exp == "y":
            clean_name = name.lower().replace(" ", "_")
            out_path = Path(f"roadmap_new_{clean_name}.md")
            export_to_markdown(res, out_path)

    elif choice == "3":
        print("\nTraining and evaluating model...")
        metrics = engine.train(verbose=True)
        print(f"\n✅ Offline Model Evaluation:")
        print(f"   • Test Ratings Evaluated: {metrics['count']:,}")
        print(f"   • Root Mean Squared Error (RMSE): {metrics['rmse']:.4f}")
        print(f"   • Mean Absolute Error (MAE):     {metrics['mae']:.4f}")

    else:
        print("Goodbye!")


def main():
    parser = argparse.ArgumentParser(
        description="AI Internship Recommendation Engine & Learning Roadmap Generator"
    )
    parser.add_argument("--evaluate", action="store_true", help="Train and evaluate Collaborative Filtering Model on test split")
    parser.add_argument("--intern-id", type=str, help="Generate roadmap for existing intern (e.g. INT-0001)")
    parser.add_argument("--new-student", action="store_true", help="Generate roadmap for a brand-new student with cold-start engine")
    parser.add_argument("--name", type=str, default="New Intern", help="Name of new student")
    parser.add_argument("--field", type=str, default="Data Science & Artificial Intelligence", help="Target career field")
    parser.add_argument("--education", type=str, default="Undergraduate Student", help="Education level")
    parser.add_argument("--major", type=str, default="Computer Science", help="Academic major")
    parser.add_argument("--size", type=int, default=8, help="Number of courses in roadmap")
    parser.add_argument("--export", type=str, help="Export roadmap to filepath (.md or .json)")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive CLI menu")

    args = parser.parse_args()

    # Initialize engine
    engine = InternshipRecommender(data_dir="data")

    if args.interactive or len(sys.argv) == 1:
        interactive_mode(engine)
        return

    if args.evaluate:
        print_banner()
        print("\n[Training & Evaluation Mode]")
        metrics = engine.train(verbose=True)
        print(f"\n📊 Final Test Set Metrics on 20% unseen holdout:")
        print(f"   • RMSE: {metrics['rmse']:.4f}")
        print(f"   • MAE:  {metrics['mae']:.4f}")
        return

    if args.intern_id:
        print_banner()
        result = engine.recommend_for_intern(
            intern_id=args.intern_id,
            target_career_field=args.field if args.field != "Data Science & Artificial Intelligence" else None,
            roadmap_size=args.size,
        )
        print_roadmap_table(result)
        if args.export:
            out_file = Path(args.export)
            if out_file.suffix.lower() == ".json":
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                print(f"✅ Exported JSON roadmap to {out_file}")
            else:
                export_to_markdown(result, out_file)
        return

    if args.new_student:
        print_banner()
        result = engine.recommend_for_new_student(
            student_name=args.name,
            target_career_field=args.field,
            education_level=args.education,
            academic_major=args.major,
            roadmap_size=args.size,
        )
        print_roadmap_table(result)
        if args.export:
            out_file = Path(args.export)
            if out_file.suffix.lower() == ".json":
                with open(out_file, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2)
                print(f"✅ Exported JSON roadmap to {out_file}")
            else:
                export_to_markdown(result, out_file)
        return


if __name__ == "__main__":
    main()
