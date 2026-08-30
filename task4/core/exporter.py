import json
from typing import Optional
from core.models import InterviewKit, Scorecard


class KitExporter:
    """Exports interview kits and scorecards to multiple distribution formats."""

    @staticmethod
    def to_markdown(kit: InterviewKit) -> str:
        """Convert an InterviewKit to a comprehensive, human-readable Markdown Interviewer Guide."""
        md = []
        md.append(f"# 📋 Intern Interview Guide & Scorecard")
        md.append(f"**Candidate:** {kit.candidate_name} | **Role:** {kit.job_title} | **Target Level:** {kit.target_level}")
        md.append(f"**Generated:** {kit.generated_at[:10]} | **Estimated Total Time:** {kit.total_duration_mins} minutes\n")
        md.append("---\n")

        # Skill Alignment & Match Analysis
        md.append("## 🎯 Skill Match & Gap Analysis")
        md.append(f"- **Overall Match Score:** **{kit.skill_analysis.match_score_percentage}%**")
        if kit.skill_analysis.matched_skills:
            md.append(f"- **Matched Core Skills:** {', '.join(kit.skill_analysis.matched_skills)}")
        if kit.skill_analysis.missing_required_skills:
            md.append(f"- **Identified Gaps (Required):** {', '.join(kit.skill_analysis.missing_required_skills)}")
        if kit.skill_analysis.missing_preferred_skills:
            md.append(f"- **Nice-to-Have Gaps:** {', '.join(kit.skill_analysis.missing_preferred_skills)}")
        if kit.skill_analysis.candidate_unique_strengths:
            md.append(f"- **Bonus Strengths:** {', '.join(kit.skill_analysis.candidate_unique_strengths)}")
        
        md.append("\n### 🔍 Recommended Interview Focus Areas:")
        for idx, fa in enumerate(kit.skill_analysis.recommended_focus_areas, 1):
            md.append(f"{idx}. {fa}")
        md.append("\n---\n")

        # Sections and Questions
        md.append("## 🧭 Interview Structure & Question Kit\n")
        for s_idx, section in enumerate(kit.sections, 1):
            md.append(f"### {section.title} ({section.duration_mins} mins)")
            md.append(f"*{section.description}*\n")

            for q_idx, q in enumerate(section.questions, 1):
                md.append(f"#### Q{s_idx}.{q_idx}: [{q.category}] {q.question}")
                md.append(f"- **Domain / Skills:** `{q.domain}` | {', '.join(q.skills) if q.skills else 'General'}")
                md.append(f"- **Difficulty:** `{q.difficulty}` | **Allocated Time:** ~{q.time_allocation_mins} mins")
                if q.project_reference:
                    md.append(f"- **Referenced Project:** *{q.project_reference}*")
                md.append(f"- **Context & Objective:** {q.context}")

                if q.expected_key_points:
                    md.append("\n**Expected Key Points:**")
                    for pt in q.expected_key_points:
                        md.append(f"  - [ ] {pt}")

                if q.follow_up_probes:
                    md.append("\n**Follow-up Probing Questions:**")
                    for probe in q.follow_up_probes:
                        md.append(f"  - *{probe}*")

                md.append("\n**Evaluation Rubric:**")
                md.append(f"  - 🔴 **Poor (1-2 pts):** {q.rubric.poor}")
                md.append(f"  - 🟡 **Good (3-4 pts):** {q.rubric.good}")
                md.append(f"  - 🟢 **Excellent (5 pts):** {q.rubric.excellent}")

                md.append("\n*Interviewer Notes & Score:* `[ 1 | 2 | 3 | 4 | 5 ]`")
                md.append("```\nNotes: \n```\n")

            md.append("---\n")

        # Evaluation & Decision Rubric
        md.append("## ⚖️ Final Hiring Decision & Rubric Sheet")
        md.append("Rate the candidate across standard intern competencies:\n")
        md.append("| Competency | Rating (1-5) | Notes |")
        md.append("| :--- | :---: | :--- |")
        md.append("| **1. CS & Technical Fundamentals** | `[ ]` | |")
        md.append("| **2. Project Ownership & Authenticity** | `[ ]` | |")
        md.append("| **3. Learning Agility & Curiosity** | `[ ]` | |")
        md.append("| **4. Communication & Collaboration** | `[ ]` | |")
        md.append("| **5. Problem Solving & Resilience** | `[ ]` | |")
        md.append("\n### Overall Recommendation:")
        md.append("- [ ] **Strong Hire:** Exceptional fundamentals, clear ownership, high curiosity.")
        md.append("- [ ] **Hire:** Solid skills matching role, coachable, positive team player.")
        md.append("- [ ] **Leaning Hire:** Good fundamentals, minor gaps in tech stack, high learning agility.")
        md.append("- [ ] **No Hire:** Significant gaps in fundamentals or poor ownership.")

        return "\n".join(md)

    @staticmethod
    def to_html(kit: InterviewKit) -> str:
        """Generate a clean, print-optimized HTML guide for web preview or PDF export."""
        sections_html = []
        for s_idx, sec in enumerate(kit.sections, 1):
            q_html = []
            for q_idx, q in enumerate(sec.questions, 1):
                key_pts = "".join([f"<li>{pt}</li>" for pt in q.expected_key_points])
                probes = "".join([f"<li><em>{pr}</em></li>" for pr in q.follow_up_probes])
                q_html.append(f"""
                <div class="question-card">
                    <div class="q-header">
                        <span class="q-badge badge-{q.category.lower().replace(' ', '-')}">{q.category}</span>
                        <span class="q-diff">{q.difficulty}</span>
                        <span class="q-time">⏱️ {q.time_allocation_mins}m</span>
                    </div>
                    <h4 class="q-title">Q{s_idx}.{q_idx}: {q.question}</h4>
                    <p class="q-context"><strong>Context:</strong> {q.context}</p>
                    
                    <div class="q-details-grid">
                        <div class="q-col">
                            <h5>Key Evaluation Points:</h5>
                            <ul>{key_pts}</ul>
                        </div>
                        <div class="q-col">
                            <h5>Follow-up Probes:</h5>
                            <ul>{probes}</ul>
                        </div>
                    </div>
                    
                    <div class="q-rubric">
                        <h5>Rubric:</h5>
                        <div class="rubric-row poor"><strong>Poor:</strong> {q.rubric.poor}</div>
                        <div class="rubric-row good"><strong>Good:</strong> {q.rubric.good}</div>
                        <div class="rubric-row excellent"><strong>Excellent:</strong> {q.rubric.excellent}</div>
                    </div>
                    
                    <div class="q-score-box">
                        <span>Score: [ 1 ] [ 2 ] [ 3 ] [ 4 ] [ 5 ]</span>
                        <div class="notes-line">Notes: ___________________________________________________________</div>
                    </div>
                </div>
                """)

            sections_html.append(f"""
            <div class="section-block">
                <div class="section-header">
                    <h3>{sec.title} <span class="sec-dur">({sec.duration_mins} mins)</span></h3>
                    <p class="sec-desc">{sec.description}</p>
                </div>
                {''.join(q_html)}
            </div>
            """)

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Interview Kit - {kit.candidate_name} - {kit.job_title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            color: #1e293b;
            line-height: 1.5;
            max-width: 900px;
            margin: 0 auto;
            padding: 30px;
            background: #ffffff;
        }}
        .header-banner {{
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 20px;
            margin-bottom: 25px;
        }}
        h1 {{ margin: 0 0 10px; color: #0f172a; font-size: 26px; }}
        .meta-bar {{ color: #64748b; font-size: 14px; display: flex; gap: 20px; flex-wrap: wrap; }}
        .match-box {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 18px;
            margin-bottom: 25px;
        }}
        .match-score {{ font-size: 22px; font-weight: bold; color: #3b82f6; }}
        .section-block {{ margin-bottom: 35px; }}
        .section-header h3 {{ margin: 0; font-size: 18px; color: #1e293b; }}
        .sec-dur {{ color: #64748b; font-size: 14px; font-weight: normal; }}
        .sec-desc {{ color: #64748b; margin: 4px 0 15px; font-size: 13px; }}
        .question-card {{
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            page-break-inside: avoid;
        }}
        .q-header {{ display: flex; gap: 10px; align-items: center; margin-bottom: 8px; }}
        .q-badge {{
            background: #e0e7ff;
            color: #4338ca;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        .q-diff {{ background: #f1f5f9; color: #475569; padding: 2px 8px; border-radius: 4px; font-size: 12px; }}
        .q-time {{ font-size: 12px; color: #64748b; }}
        .q-title {{ margin: 0 0 8px; font-size: 15px; color: #0f172a; }}
        .q-context {{ font-size: 13px; color: #475569; margin: 0 0 12px; }}
        .q-details-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 12px; font-size: 13px; }}
        .q-col h5, .q-rubric h5 {{ margin: 0 0 4px; font-size: 12px; text-transform: uppercase; color: #64748b; }}
        .q-col ul {{ margin: 0; padding-left: 18px; }}
        .q-rubric {{ background: #f8fafc; padding: 10px; border-radius: 6px; font-size: 12px; margin-bottom: 10px; }}
        .rubric-row {{ margin-bottom: 4px; }}
        .rubric-row.poor {{ color: #dc2626; }}
        .rubric-row.good {{ color: #d97706; }}
        .rubric-row.excellent {{ color: #16a34a; }}
        .q-score-box {{
            border-top: 1px dashed #cbd5e1;
            padding-top: 8px;
            font-size: 13px;
            color: #334155;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        @media print {{
            body {{ padding: 0; font-size: 12px; }}
            .question-card {{ break-inside: avoid; }}
        }}
    </style>
</head>
<body>
    <div class="header-banner">
        <h1>Intern Interview Guide & Scorecard</h1>
        <div class="meta-bar">
            <span><strong>Candidate:</strong> {kit.candidate_name}</span>
            <span><strong>Position:</strong> {kit.job_title}</span>
            <span><strong>Target Level:</strong> {kit.target_level}</span>
            <span><strong>Duration:</strong> {kit.total_duration_mins} mins</span>
        </div>
    </div>
    
    <div class="match-box">
        <div>Skill Match Score: <span class="match-score">{kit.skill_analysis.match_score_percentage}%</span></div>
        <p style="margin: 6px 0 0; font-size: 13px;"><strong>Matched Skills:</strong> {', '.join(kit.skill_analysis.matched_skills)}</p>
        <p style="margin: 4px 0 0; font-size: 13px;"><strong>Identified Gap Focus:</strong> {', '.join(kit.skill_analysis.missing_required_skills) if kit.skill_analysis.missing_required_skills else 'None (Fully Matched)'}</p>
    </div>
    
    {''.join(sections_html)}
</body>
</html>"""
        return html_content

    @staticmethod
    def to_json(kit: InterviewKit) -> str:
        return kit.model_dump_json(indent=2)
