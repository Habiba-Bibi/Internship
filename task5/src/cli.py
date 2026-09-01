"""
cli.py
Command-Line Interface for Intern Skills & Industry Demand Gap Analysis.
"""

import sys
import os
import argparse
import json
import pandas as pd
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
sys.path.insert(0, BASE_DIR)

from src.generate_data import main as run_generate
from src.nlp_clustering_pipeline import SkillGapClusteringEngine, clean_tech_text

def get_engine() -> SkillGapClusteringEngine:
    engine = SkillGapClusteringEngine()
    try:
        engine.load_artifacts()
    except Exception:
        print("[*] Model artifacts not found. Training model now...")
        engine.train()
    return engine


def handle_generate(args):
    print("Generating fresh datasets...")
    run_generate()


def handle_train(args):
    print(f"Training NLP & K-Means clustering pipeline with k={args.clusters}...")
    engine = SkillGapClusteringEngine(n_clusters=args.clusters)
    engine.train()
    print("Training finished successfully.")


def handle_clusters(args):
    engine = get_engine()
    print("\n" + "="*80)
    print(" INDUSTRY JOB MARKET CLUSTERS (NLP TF-IDF + K-MEANS) ")
    print("="*80)
    for c_id, profile in engine.cluster_profiles.items():
        print(f"\n[Cluster {c_id}] {profile['cluster_name']}")
        print(f"  - Dominant Domain:  {profile['dominant_domain']}")
        print(f"  - Job Postings:     {profile['job_count']} | Interns Mapped: {profile['intern_count']}")
        print(f"  - Top TF-IDF Terms: {', '.join(profile['top_terms'][:6])}")
        print(f"  - Top Roles:        {', '.join(profile['top_roles'][:3])}")
        dem_skills = list(profile['top_demanded_skills'].keys())[:5]
        print(f"  - Key Demands:      {', '.join(dem_skills)}")
    print("\n" + "="*80)


def handle_analyze_intern(args):
    engine = get_engine()
    res = engine.analyze_intern_by_id(args.intern_id)
    if not res:
        print(f"Error: Intern ID '{args.intern_id}' not found in database.")
        return

    gap = res["gap_analysis"]
    tp = gap["training_plan"]

    print("\n" + "="*80)
    print(f" INTERN SKILL GAP REPORT: {res['name']} ({res['intern_id']})")
    print("="*80)
    print(f"University:       {res['university']} | {res['degree']}")
    print(f"Target Role:      {res['target_role']} ({res['target_domain']})")
    print(f"Assigned Cluster: {res['cluster_name']}")
    print(f"Readiness Score:  {gap['readiness_score']}% (Match Ratio: {gap['match_ratio']})")
    print(f"Semantic Sim:     {gap['cosine_similarity']}")

    print("\n--- SKILL BREAKDOWN ---")
    print(f"[+] Matched Skills ({len(gap['matched_skills'])}):")
    print(f"    {', '.join(gap['matched_skills']) if gap['matched_skills'] else 'None'}")
    print(f"[-] Missing Critical Skills ({len(gap['missing_critical_skills'])}):")
    print(f"    {', '.join(gap['missing_critical_skills']) if gap['missing_critical_skills'] else 'None'}")
    print(f"[*] Missing Preferred Skills ({len(gap['missing_preferred_skills'])}):")
    print(f"    {', '.join(gap['missing_preferred_skills']) if gap['missing_preferred_skills'] else 'None'}")

    if gap["proficiency_gaps"]:
        print(f"[!] Proficiency Deficits ({len(gap['proficiency_gaps'])}):")
        for pg in gap["proficiency_gaps"]:
            print(f"    - {pg['skill']}: Current Level {pg['current_level']}/5 (Target: {pg['target_level']}/5)")

    print("\n" + "-"*80)
    print(" PERSONALIZED 12-WEEK TRAINING ROADMAP")
    print("-"*80)
    print(f"Estimated Duration: {tp['estimated_weeks']} Weeks | {tp['estimated_study_hours']} Hours of Study")
    print(f"Expected Readiness Boost: {tp['expected_readiness_boost']}")

    for phase in tp["phases"]:
        print(f"\n>> {phase['title']}")
        print(f"   Goal: {phase['description']}")
        for mod in phase["modules"]:
            print(f"   * [{mod['priority']}] {mod['skill']}")
            print(f"     Course:  {mod['course_title']} ({mod['platform']})")
            print(f"     Project: {mod['project']}")
            print(f"     Cert:    {mod['certification']}")
    print("\n" + "="*80)


def handle_analyze_custom(args):
    engine = get_engine()
    res = engine.analyze_custom_profile(
        skills_input=args.skills,
        target_role=args.role,
        bio_input=args.bio or ""
    )
    gap = res["gap_analysis"]
    tp = gap["training_plan"]

    print("\n" + "="*80)
    print(f" CUSTOM PROFILE ANALYSIS: Target Role = {res['target_role']}")
    print("="*80)
    print(f"Input Skills:     {', '.join(res['skills'])}")
    print(f"Matched Domain:   {res['target_domain']}")
    print(f"Mapped Cluster:   {res['cluster_name']}")
    print(f"Readiness Score:  {gap['readiness_score']}%")
    print(f"Matched Skills:   {', '.join(gap['matched_skills']) if gap['matched_skills'] else 'None'}")
    print(f"Critical Gaps:    {', '.join(gap['missing_critical_skills']) if gap['missing_critical_skills'] else 'None'}")
    print(f"Preferred Gaps:   {', '.join(gap['missing_preferred_skills']) if gap['missing_preferred_skills'] else 'None'}")

    print("\n--- RECOMMENDED FIRST-STEP COURSES ---")
    for phase in tp["phases"][:2]:
        for mod in phase["modules"][:2]:
            print(f"- {mod['skill']}: {mod['course_title']} ({mod['platform']})")
    print("\n" + "="*80)


def handle_export_summary(args):
    engine = get_engine()
    print("Generating bulk gap analysis report for all interns...")

    report_rows = []
    for _, row in engine.interns_df.iterrows():
        res = engine.analyze_intern_by_id(row["intern_id"])
        if res:
            g = res["gap_analysis"]
            report_rows.append({
                "intern_id": res["intern_id"],
                "name": res["name"],
                "university": res["university"],
                "target_domain": res["target_domain"],
                "target_role": res["target_role"],
                "cluster_name": res["cluster_name"],
                "readiness_score_pct": g["readiness_score"],
                "matched_skills_count": len(g["matched_skills"]),
                "matched_skills": "; ".join(g["matched_skills"]),
                "missing_critical_count": len(g["missing_critical_skills"]),
                "missing_critical_skills": "; ".join(g["missing_critical_skills"]),
                "missing_preferred_skills": "; ".join(g["missing_preferred_skills"]),
                "proficiency_deficits_count": len(g["proficiency_gaps"])
            })

    out_df = pd.DataFrame(report_rows)
    out_path = os.path.join(DATA_DIR, "intern_gap_analysis_report.csv")
    out_df.to_csv(out_path, index=False)
    print(f"Bulk report saved to: {out_path} ({len(out_df)} interns evaluated)")


def main():
    parser = argparse.ArgumentParser(description="Intern Skills & Industry Gap Analyzer CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Subcommand: generate
    subparsers.add_parser("generate", help="Generate fresh synthetic datasets")

    # Subcommand: train
    train_p = subparsers.add_parser("train", help="Train TF-IDF and K-Means Clustering model")
    train_p.add_argument("--clusters", type=int, default=8, help="Number of K-Means clusters (default: 8)")

    # Subcommand: clusters
    subparsers.add_parser("clusters", help="Display discovered job market clusters")

    # Subcommand: analyze-intern
    intern_p = subparsers.add_parser("analyze-intern", help="Analyze skills and gaps for an intern ID")
    intern_p.add_argument("intern_id", type=str, help="Intern ID (e.g. INT-1001)")

    # Subcommand: analyze-custom
    custom_p = subparsers.add_parser("analyze-custom", help="Analyze custom skills set and target role")
    custom_p.add_argument("--skills", type=str, required=True, help="Comma-separated list of skills")
    custom_p.add_argument("--role", type=str, default="Machine Learning Engineer", help="Target Job Role")
    custom_p.add_argument("--bio", type=str, default="", help="Candidate bio/resume text")

    # Subcommand: export-summary
    subparsers.add_parser("export-summary", help="Export bulk gap analysis report to CSV")

    args = parser.parse_args()

    if args.command == "generate":
        handle_generate(args)
    elif args.command == "train":
        handle_train(args)
    elif args.command == "clusters":
        handle_clusters(args)
    elif args.command == "analyze-intern":
        handle_analyze_intern(args)
    elif args.command == "analyze-custom":
        handle_analyze_custom(args)
    elif args.command == "export-summary":
        handle_export_summary(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
