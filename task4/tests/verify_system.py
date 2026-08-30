import httpx
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

BASE_URL = "http://localhost:8000"


def test_full_system():
    print("Testing InternAI System Endpoints...")
    client = httpx.Client(base_url=BASE_URL, timeout=10.0)

    # 1. Test Static Frontend
    r_index = client.get("/")
    assert r_index.status_code == 200, f"Failed index.html: {r_index.status_code}"
    assert "InternAI" in r_index.text
    print("✅ Static frontend index.html served successfully")

    r_css = client.get("/css/style.css")
    assert r_css.status_code == 200, f"Failed style.css: {r_css.status_code}"
    assert "--bg-main" in r_css.text
    print("✅ CSS stylesheet served successfully")

    r_js = client.get("/js/app.js")
    assert r_js.status_code == 200, f"Failed app.js: {r_js.status_code}"
    assert "generateInterviewKit" in r_js.text
    print("✅ JavaScript app logic served successfully")

    # 2. Test Candidates
    r_cands = client.get("/api/candidates")
    assert r_cands.status_code == 200
    cands = r_cands.json()
    assert len(cands) >= 5
    alex = next(c for c in cands if "Alex" in c["name"])
    print(f"✅ Candidates API: {len(cands)} candidates loaded (e.g. {alex['name']})")

    # 3. Test Jobs
    r_jobs = client.get("/api/jobs")
    assert r_jobs.status_code == 200
    jobs = r_jobs.json()
    assert len(jobs) >= 5
    fe_job = next(j for j in jobs if "Frontend" in j["title"])
    print(f"✅ Jobs API: {len(jobs)} jobs loaded (e.g. {fe_job['title']})")

    # 4. Test Match Analysis
    r_match = client.post("/api/match-analysis", json={
        "candidate_id": alex["id"],
        "job_id": fe_job["id"]
    })
    assert r_match.status_code == 200
    match_data = r_match.json()
    assert match_data["match_score_percentage"] >= 80.0
    print(f"✅ Match Analysis: Score = {match_data['match_score_percentage']}% | Matched = {match_data['matched_skills']}")

    # 5. Test Generate Kit
    gen_payload = {
        "candidate_id": alex["id"],
        "job_id": fe_job["id"],
        "num_resume_deep_dive": 2,
        "num_technical": 4,
        "num_behavioral": 3,
        "num_scenario": 1,
        "difficulty": "Standard Intern",
        "llm_provider": "mock"
    }
    r_gen = client.post("/api/generate-kit", json=gen_payload)
    assert r_gen.status_code == 200
    kit = r_gen.json()
    kit_id = kit["id"]
    assert len(kit["sections"]) >= 5
    assert len(kit["questions"]) >= 10
    print(f"✅ Interview Kit Generated: ID = {kit_id} | Total Qs = {len(kit['questions'])} | Duration = {kit['total_duration_mins']} mins")

    # 6. Test Single Question Re-roll
    r_regen = client.post("/api/regenerate-question", json={
        "category": "Technical",
        "domain": "Frontend Architecture",
        "skill": "React",
        "difficulty": "Standard Intern",
        "candidate_name": alex["name"],
        "job_title": fe_job["title"]
    })
    assert r_regen.status_code == 200
    new_q = r_regen.json()
    assert new_q["category"] == "Technical"
    print(f"✅ Question Re-roll: Generated new question [{new_q['id']}]: {new_q['question'][:60]}...")

    # 7. Test Scorecard Submission
    ratings = [
        {"question_id": q["id"], "score": 5 if i % 2 == 0 else 4, "notes": "Solid answer"}
        for i, q in enumerate(kit["questions"][:5])
    ]
    r_sc = client.post("/api/scorecard", json={
        "kit_id": kit_id,
        "candidate_name": alex["name"],
        "job_title": fe_job["title"],
        "interviewer_name": "Senior Staff Engineer",
        "ratings": ratings,
        "final_feedback": "Exceptional understanding of frontend lifecycle and component rendering."
    })
    assert r_sc.status_code == 200
    scorecard = r_sc.json()
    assert scorecard["overall_score"] >= 4.0
    assert scorecard["recommendation"] in ["Strong Hire", "Hire"]
    print(f"✅ Scorecard Evaluated: Overall = {scorecard['overall_score']}/5.0 | Recommendation = {scorecard['recommendation']}")

    # 8. Test Export Endpoints
    r_md = client.get(f"/api/export/{kit_id}?format=markdown")
    assert r_md.status_code == 200
    assert "Intern Interview Guide" in r_md.text
    print("✅ Export Markdown: Success")

    r_html = client.get(f"/api/export/{kit_id}?format=html")
    assert r_html.status_code == 200
    assert "<!DOCTYPE html>" in r_html.text
    print("✅ Export HTML: Success")

    r_json = client.get(f"/api/export/{kit_id}?format=json")
    assert r_json.status_code == 200
    assert r_json.json()["id"] == kit_id
    print("✅ Export JSON: Success")

    # 9. Test Question Bank Search
    r_bank = client.get("/api/questions?category=Technical&difficulty=Standard+Intern")
    assert r_bank.status_code == 200
    bank_qs = r_bank.json()
    assert len(bank_qs) >= 1
    print(f"✅ Question Bank Filtering: Found {len(bank_qs)} Standard Intern technical questions")

    print("\n🎉 ALL 9 END-TO-END SYSTEM INTEGRATION TESTS PASSED PERFECTLY!\n")

if __name__ == "__main__":
    test_full_system()
