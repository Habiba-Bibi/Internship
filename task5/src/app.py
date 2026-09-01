"""
app.py
Flask Web Application & REST API Server for Intern Skills
and Industry Demand Gap Identification Platform.
"""

import os
import sys
import json
from flask import Flask, render_template, request, jsonify, send_file

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from src.nlp_clustering_pipeline import SkillGapClusteringEngine

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

# Global engine singleton
engine = SkillGapClusteringEngine()

def init_engine():
    global engine
    try:
        engine.load_artifacts()
        print("[*] SkillGapClusteringEngine artifacts loaded successfully.")
    except Exception as e:
        print(f"[*] Artifact loading failed ({e}). Training fresh engine...")
        engine.train()

init_engine()


@app.route("/")
def index():
    """Renders the main single-page web dashboard."""
    return render_template("index.html")


@app.route("/api/overview", methods=["GET"])
def api_overview():
    """Returns macro metrics, supply vs demand deficits, and domain distribution."""
    try:
        overview = engine.get_market_overview()
        return jsonify({"status": "success", "data": overview})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/clusters", methods=["GET"])
def api_clusters():
    """Returns cluster metadata, centroid keywords, and 2D PCA coordinates."""
    try:
        data = engine.get_cluster_intelligence()
        return jsonify({"status": "success", "data": data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/interns", methods=["GET"])
def api_interns():
    """Returns list of all interns with basic metadata and gap summaries."""
    try:
        domain_filter = request.args.get("domain", "").strip()
        search_query = request.args.get("search", "").strip().lower()
        cluster_filter = request.args.get("cluster", "").strip()

        interns = []
        for _, row in engine.interns_df.iterrows():
            if domain_filter and row["target_domain"] != domain_filter:
                continue
            if cluster_filter and str(row["cluster_id"]) != cluster_filter:
                continue
            if search_query:
                combined = f"{row['name']} {row['intern_id']} {row['university']} {row['target_role']} {row['skills']}".lower()
                if search_query not in combined:
                    continue

            interns.append({
                "intern_id": row["intern_id"],
                "name": row["name"],
                "email": row["email"],
                "university": row["university"],
                "degree": row["degree"],
                "target_domain": row["target_domain"],
                "target_role": row["target_role"],
                "experience_years": float(row["experience_years"]),
                "skills": engine.parse_skill_list(row["skills"]),
                "skill_count": int(row["skill_count"]),
                "cluster_id": int(row["cluster_id"]),
                "cluster_name": engine.cluster_profiles.get(int(row["cluster_id"]), {}).get("cluster_name", f"Cluster {row['cluster_id']}")
            })

        return jsonify({
            "status": "success",
            "total": len(interns),
            "data": interns
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/intern/<intern_id>", methods=["GET"])
def api_intern_detail(intern_id: str):
    """Returns comprehensive skill gap analysis, radar chart points, and training roadmap."""
    try:
        result = engine.analyze_intern_by_id(intern_id)
        if not result:
            return jsonify({"status": "error", "message": f"Intern {intern_id} not found"}), 404

        # Generate radar chart data (Intern Proficiency vs Benchmark Required Level)
        gap_data = result["gap_analysis"]
        all_key_skills = list(dict.fromkeys(
            gap_data["matched_skills"] + gap_data["missing_critical_skills"][:4] + gap_data["missing_preferred_skills"][:2]
        ))[:7]

        radar_labels = all_key_skills
        intern_scores = []
        benchmark_scores = []

        for skill in all_key_skills:
            intern_scores.append(result["proficiencies"].get(skill, 0))
            if skill in gap_data["matched_skills"]:
                benchmark_scores.append(4)
            elif skill in gap_data["missing_critical_skills"]:
                benchmark_scores.append(4)
            else:
                benchmark_scores.append(3)

        result["radar_chart"] = {
            "labels": radar_labels,
            "intern_scores": intern_scores,
            "benchmark_scores": benchmark_scores
        }

        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/jobs", methods=["GET"])
def api_jobs():
    """Returns filterable job postings database."""
    try:
        domain_filter = request.args.get("domain", "").strip()
        search_query = request.args.get("search", "").strip().lower()

        jobs = []
        for _, row in engine.jobs_df.iterrows():
            if domain_filter and row["domain"] != domain_filter:
                continue
            if search_query:
                combined = f"{row['job_title']} {row['company']} {row['required_skills']} {row['sector']}".lower()
                if search_query not in combined:
                    continue

            jobs.append({
                "job_id": row["job_id"],
                "job_title": row["job_title"],
                "company": row["company"],
                "location": row["location"],
                "sector": row["sector"],
                "domain": row["domain"],
                "experience_level": row["experience_level"],
                "required_skills": engine.parse_skill_list(row["required_skills"]),
                "preferred_skills": engine.parse_skill_list(row["preferred_skills"]),
                "tools_technologies": engine.parse_skill_list(row["tools_technologies"]),
                "salary_range": row["salary_range"],
                "cluster_id": int(row["cluster_id"]),
                "cluster_name": engine.cluster_profiles.get(int(row["cluster_id"]), {}).get("cluster_name", f"Cluster {row['cluster_id']}")
            })

        return jsonify({
            "status": "success",
            "total": len(jobs),
            "data": jobs
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/analyze-custom", methods=["POST"])
def api_analyze_custom():
    """Accepts custom resume/skills input and performs live instant gap analysis."""
    try:
        payload = request.get_json() or {}
        skills_input = payload.get("skills", "")
        target_role = payload.get("target_role", "")
        bio_input = payload.get("bio", "")

        if not skills_input and not bio_input:
            return jsonify({"status": "error", "message": "Please provide skills or resume text"}), 400

        result = engine.analyze_custom_profile(
            skills_input=skills_input,
            target_role=target_role,
            bio_input=bio_input
        )

        # Build radar data
        gap_data = result["gap_analysis"]
        all_key_skills = list(dict.fromkeys(
            gap_data["matched_skills"] + gap_data["missing_critical_skills"][:4] + gap_data["missing_preferred_skills"][:2]
        ))[:7]

        intern_scores = [3 if s in gap_data["matched_skills"] else 0 for s in all_key_skills]
        benchmark_scores = [4 if (s in gap_data["matched_skills"] or s in gap_data["missing_critical_skills"]) else 3 for s in all_key_skills]

        result["radar_chart"] = {
            "labels": all_key_skills,
            "intern_scores": intern_scores,
            "benchmark_scores": benchmark_scores
        }

        return jsonify({"status": "success", "data": result})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/courses", methods=["GET"])
def api_courses():
    """Returns full catalog of curated courses, project ideas, and certifications."""
    try:
        return jsonify({"status": "success", "data": engine.course_catalog})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
