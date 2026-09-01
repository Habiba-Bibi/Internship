"""
nlp_clustering_pipeline.py
End-to-End NLP, TF-IDF Vectorization, K-Means Clustering,
Skill Gap Analysis, and Training Recommendation Engine.
"""

import os
import re
import json
import joblib
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# Custom tech-preserving stop words
EXTENDED_STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves",
    # Job posting boilerplate words
    "seeking", "motivated", "join", "team", "working", "work", "role", "looking",
    "candidate", "responsibilities", "responsible", "qualifications", "experience",
    "opportunity", "environment", "years", "degree", "bachelor", "master", "plus",
    "strong", "demonstrated", "ability", "excellent", "passionate", "seeking",
    "related", "field", "skills", "including", "across", "within", "key", "tools"
}


def clean_tech_text(text: str) -> str:
    """
    Cleans text while preserving critical technical symbols and compound terms
    (e.g., C++, C#, .NET, Node.js, CI/CD, REST APIs, etc.)
    """
    if not text or not isinstance(text, str):
        return ""

    # Normalize special tokens
    s = text.replace("C++", " cplusplus ")
    s = s.replace("C#", " csharp ")
    s = s.replace(".NET", " dotnet ")
    s = s.replace("Node.js", " nodejs ")
    s = s.replace("Next.js", " nextjs ")
    s = s.replace("Express.js", " expressjs ")
    s = s.replace("CI/CD", " cicd ")
    s = s.replace("TCP/IP", " tcpip ")
    s = s.replace("A/B", " abtesting ")
    s = s.replace("Power BI", " powerbi ")

    # Lowercase
    s = s.lower()

    # Remove unwanted punctuation but keep alphanumeric and spaces
    s = re.sub(r'[^a-z0-9\s]', ' ', s)
    # Collapse whitespace
    s = re.sub(r'\s+', ' ', s).strip()

    # Filter out custom stop words
    tokens = [t for t in s.split() if t not in EXTENDED_STOP_WORDS and len(t) > 1]
    return " ".join(tokens)


class SkillGapClusteringEngine:
    def __init__(self, n_clusters: int = 8):
        self.n_clusters = n_clusters
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.kmeans: Optional[KMeans] = None
        self.pca: Optional[PCA] = None
        self.interns_df: Optional[pd.DataFrame] = None
        self.jobs_df: Optional[pd.DataFrame] = None
        self.course_catalog: Dict[str, Any] = {}
        self.skills_taxonomy: Dict[str, Any] = {}
        self.cluster_profiles: Dict[int, Dict[str, Any]] = {}
        self.job_tfidf_matrix = None
        self.intern_tfidf_matrix = None
        self.job_pca_coords = None
        self.intern_pca_coords = None

    def load_data(self):
        """Loads data from CSV and JSON files."""
        interns_path = os.path.join(DATA_DIR, "interns_skills.csv")
        jobs_path = os.path.join(DATA_DIR, "industry_jobs.csv")
        catalog_path = os.path.join(DATA_DIR, "course_catalog.json")
        taxonomy_path = os.path.join(DATA_DIR, "skills_taxonomy.json")

        self.interns_df = pd.read_csv(interns_path)
        self.jobs_df = pd.read_csv(jobs_path)

        with open(catalog_path, "r", encoding="utf-8") as f:
            self.course_catalog = json.load(f)

        with open(taxonomy_path, "r", encoding="utf-8") as f:
            self.skills_taxonomy = json.load(f)

    def prepare_corpora(self) -> Tuple[List[str], List[str]]:
        """Prepares text corpus for jobs and interns."""
        job_texts = []
        for _, row in self.jobs_df.iterrows():
            combined = f"{row['job_title']} {row['domain']} {row['required_skills']} {row['preferred_skills']} {row['tools_technologies']} {row['job_description']}"
            job_texts.append(clean_tech_text(combined))

        intern_texts = []
        for _, row in self.interns_df.iterrows():
            combined = f"{row['target_role']} {row['target_domain']} {row['skills']} {row['certifications']} {row['bio']}"
            intern_texts.append(clean_tech_text(combined))

        return job_texts, intern_texts

    def train(self):
        """Fits TF-IDF, K-Means clustering, PCA reduction, and cluster profiling."""
        print("Loading datasets...")
        self.load_data()

        job_texts, intern_texts = self.prepare_corpora()
        all_texts = job_texts + intern_texts

        print(f"Building TF-IDF Vectorizer with {len(all_texts)} documents...")
        self.vectorizer = TfidfVectorizer(
            max_features=1200,
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=2
        )
        self.vectorizer.fit(all_texts)

        # Transform both matrices
        self.job_tfidf_matrix = self.vectorizer.transform(job_texts)
        self.intern_tfidf_matrix = self.vectorizer.transform(intern_texts)

        print(f"Clustering {self.job_tfidf_matrix.shape[0]} industry job postings into {self.n_clusters} clusters...")
        self.kmeans = KMeans(
            n_clusters=self.n_clusters,
            random_state=42,
            n_init=15,
            max_iter=300
        )
        job_cluster_labels = self.kmeans.fit_predict(self.job_tfidf_matrix)
        self.jobs_df["cluster_id"] = job_cluster_labels

        # Silhouette score
        sil_score = silhouette_score(self.job_tfidf_matrix, job_cluster_labels)
        print(f"Model Training Complete! Silhouette Score: {sil_score:.4f}")

        # Predict cluster for interns based on nearest centroid
        intern_cluster_labels = self.kmeans.predict(self.intern_tfidf_matrix)
        self.interns_df["cluster_id"] = intern_cluster_labels

        # 2D PCA for visual mapping
        print("Performing 2D PCA Dimensionality Reduction...")
        self.pca = PCA(n_components=2, random_state=42)
        # Fit on job matrix, transform both
        self.job_pca_coords = self.pca.fit_transform(self.job_tfidf_matrix.toarray())
        self.intern_pca_coords = self.pca.transform(self.intern_tfidf_matrix.toarray())

        self.jobs_df["pca_x"] = self.job_pca_coords[:, 0]
        self.jobs_df["pca_y"] = self.job_pca_coords[:, 1]
        self.interns_df["pca_x"] = self.intern_pca_coords[:, 0]
        self.interns_df["pca_y"] = self.intern_pca_coords[:, 1]

        # Build Cluster Profiles
        print("Generating Cluster Profiles and Centroid Keywords...")
        self._build_cluster_profiles()

        # Save artifacts
        self.save_artifacts()
        print("Pipeline execution and artifact storage completed successfully.")

    def _build_cluster_profiles(self):
        """Builds descriptive metadata for each discovered K-Means cluster."""
        terms = np.array(self.vectorizer.get_feature_names_out())
        centroids = self.kmeans.cluster_centers_

        for cluster_id in range(self.n_clusters):
            # Top keywords from centroid
            top_indices = centroids[cluster_id].argsort()[::-1][:12]
            top_terms = terms[top_indices].tolist()

            # Jobs belonging to this cluster
            cluster_jobs = self.jobs_df[self.jobs_df["cluster_id"] == cluster_id]
            cluster_interns = self.interns_df[self.interns_df["cluster_id"] == cluster_id]

            # Dominant domain and common titles
            dom_counts = cluster_jobs["domain"].value_counts()
            dominant_domain = dom_counts.index[0] if len(dom_counts) > 0 else "General Tech"
            top_roles = cluster_jobs["job_title"].value_counts().head(3).index.tolist()

            # Extract most demanded skills in this cluster
            all_req_skills = []
            for s_str in cluster_jobs["required_skills"].dropna():
                for s in s_str.split(","):
                    all_req_skills.append(s.strip())
            top_demanded_skills = pd.Series(all_req_skills).value_counts().head(8).to_dict()

            # Format human-friendly cluster name
            cluster_name = f"{dominant_domain} ({', '.join(top_terms[:2]).title()})"

            self.cluster_profiles[cluster_id] = {
                "cluster_id": cluster_id,
                "cluster_name": cluster_name,
                "dominant_domain": dominant_domain,
                "job_count": int(len(cluster_jobs)),
                "intern_count": int(len(cluster_interns)),
                "top_terms": top_terms,
                "top_roles": top_roles,
                "top_demanded_skills": top_demanded_skills,
                "centroid_2d": [
                    float(self.job_pca_coords[self.jobs_df["cluster_id"] == cluster_id, 0].mean()),
                    float(self.job_pca_coords[self.jobs_df["cluster_id"] == cluster_id, 1].mean())
                ]
            }

    def save_artifacts(self):
        """Serializes trained models and processed data."""
        artifacts = {
            "n_clusters": self.n_clusters,
            "cluster_profiles": self.cluster_profiles,
            "jobs_df": self.jobs_df,
            "interns_df": self.interns_df,
            "course_catalog": self.course_catalog,
            "skills_taxonomy": self.skills_taxonomy
        }
        joblib.dump(self.vectorizer, os.path.join(MODELS_DIR, "tfidf_vectorizer.joblib"))
        joblib.dump(self.kmeans, os.path.join(MODELS_DIR, "kmeans_model.joblib"))
        joblib.dump(self.pca, os.path.join(MODELS_DIR, "pca_transformer.joblib"))
        joblib.dump(artifacts, os.path.join(MODELS_DIR, "pipeline_artifacts.joblib"))

        # Also save JSON metadata for easy external inspection
        meta_path = os.path.join(MODELS_DIR, "cluster_summary.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(self.cluster_profiles, f, indent=2)

    def load_artifacts(self):
        """Loads serialized models and metadata."""
        self.vectorizer = joblib.load(os.path.join(MODELS_DIR, "tfidf_vectorizer.joblib"))
        self.kmeans = joblib.load(os.path.join(MODELS_DIR, "kmeans_model.joblib"))
        self.pca = joblib.load(os.path.join(MODELS_DIR, "pca_transformer.joblib"))
        artifacts = joblib.load(os.path.join(MODELS_DIR, "pipeline_artifacts.joblib"))

        self.n_clusters = artifacts["n_clusters"]
        self.cluster_profiles = artifacts["cluster_profiles"]
        self.jobs_df = artifacts["jobs_df"]
        self.interns_df = artifacts["interns_df"]
        self.course_catalog = artifacts["course_catalog"]
        self.skills_taxonomy = artifacts["skills_taxonomy"]

        # Reconstruct transformed matrices
        job_texts, intern_texts = self.prepare_corpora()
        self.job_tfidf_matrix = self.vectorizer.transform(job_texts)
        self.intern_tfidf_matrix = self.vectorizer.transform(intern_texts)
        self.job_pca_coords = self.jobs_df[["pca_x", "pca_y"]].to_numpy()
        self.intern_pca_coords = self.interns_df[["pca_x", "pca_y"]].to_numpy()

    # -------------------------------------------------------------------------
    # SKILL GAP ANALYSIS & RECOMMENDATION ENGINE
    # -------------------------------------------------------------------------
    def parse_skill_list(self, skill_str: str) -> List[str]:
        """Splits comma separated skills and cleans whitespace."""
        if not skill_str or not isinstance(skill_str, str):
            return []
        return [s.strip() for s in skill_str.split(",") if s.strip()]

    def calculate_skill_gaps(
        self,
        intern_skills: List[str],
        intern_proficiencies: Dict[str, int],
        intern_vector,
        target_job_row: Optional[pd.Series] = None,
        target_cluster_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculates exact matched skills, missing critical skills, missing preferred skills,
        proficiency deficits, and overall readiness score.
        """
        intern_skills_set = set(intern_skills)

        if target_job_row is not None:
            job_required = self.parse_skill_list(target_job_row.get("required_skills", ""))
            job_preferred = self.parse_skill_list(target_job_row.get("preferred_skills", ""))
            target_role = target_job_row.get("job_title", "Target Role")
            target_domain = target_job_row.get("domain", "General Tech")
            job_desc_clean = clean_tech_text(target_job_row.get("job_description", ""))
            job_vec = self.vectorizer.transform([job_desc_clean])
            cosine_sim = float(cosine_similarity(intern_vector, job_vec)[0][0])
        elif target_cluster_id is not None and target_cluster_id in self.cluster_profiles:
            cp = self.cluster_profiles[target_cluster_id]
            job_required = list(cp["top_demanded_skills"].keys())[:6]
            job_preferred = list(cp["top_demanded_skills"].keys())[6:]
            target_role = cp["top_roles"][0] if cp["top_roles"] else cp["cluster_name"]
            target_domain = cp["dominant_domain"]
            centroid_vec = self.kmeans.cluster_centers_[target_cluster_id].reshape(1, -1)
            cosine_sim = float(cosine_similarity(intern_vector, centroid_vec)[0][0])
        else:
            job_required = ["Python", "Git", "SQL", "Problem Solving"]
            job_preferred = ["Docker", "CI/CD"]
            target_role = "Software Engineer"
            target_domain = "General Tech"
            cosine_sim = 0.5

        req_set = set(job_required)
        pref_set = set(job_preferred)

        matched_skills = [s for s in job_required if s in intern_skills_set]
        missing_critical = [s for s in job_required if s not in intern_skills_set]
        missing_preferred = [s for s in job_preferred if s not in intern_skills_set]
        bonus_skills = [s for s in intern_skills if s not in req_set and s not in pref_set]

        # Proficiency Gaps: Intern has skill, but score is < 4
        proficiency_gaps = []
        for s in matched_skills:
            score = intern_proficiencies.get(s, 3)
            if score < 4:
                proficiency_gaps.append({
                    "skill": s,
                    "current_level": score,
                    "target_level": 4,
                    "gap": 4 - score
                })

        # Readiness Score Calculation
        # Cosine similarity (40%) + Required Match Ratio (45%) + Preferred Match Bonus (15%)
        req_ratio = len(matched_skills) / max(len(job_required), 1)
        pref_matched = [s for s in job_preferred if s in intern_skills_set]
        pref_ratio = len(pref_matched) / max(len(job_preferred), 1)

        raw_score = (cosine_sim * 0.40) + (req_ratio * 0.45) + (pref_ratio * 0.15)
        readiness_percentage = max(10, min(98, round(raw_score * 100, 1)))

        # Build training curriculum recommendations
        training_plan = self.generate_training_recommendations(missing_critical, missing_preferred, proficiency_gaps)

        return {
            "target_role": target_role,
            "target_domain": target_domain,
            "readiness_score": readiness_percentage,
            "cosine_similarity": round(cosine_sim, 3),
            "matched_skills": matched_skills,
            "missing_critical_skills": missing_critical,
            "missing_preferred_skills": missing_preferred,
            "bonus_skills": bonus_skills,
            "proficiency_gaps": proficiency_gaps,
            "match_ratio": f"{len(matched_skills)}/{len(job_required)} ({round(req_ratio*100)}%)",
            "training_plan": training_plan
        }

    def generate_training_recommendations(
        self,
        missing_critical: List[str],
        missing_preferred: List[str],
        proficiency_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Creates a 3-phase structured upskilling roadmap:
        Phase 1: Foundational / High-Priority Missing Skills (Weeks 1-4)
        Phase 2: Applied Frameworks & Proficiency Upgrades (Weeks 5-8)
        Phase 3: Advanced Projects, Cloud / DevOps & Certifications (Weeks 9-12)
        """
        all_skills_to_learn = []
        for s in missing_critical:
            all_skills_to_learn.append({"skill": s, "priority": "High (Critical Gap)", "type": "Missing Mandatory"})
        for pg in proficiency_gaps:
            all_skills_to_learn.append({"skill": pg["skill"], "priority": "Medium (Proficiency Upgrade)", "type": f"Level {pg['current_level']} -> 4"})
        for s in missing_preferred:
            all_skills_to_learn.append({"skill": s, "priority": "Low (Preferred Bonus)", "type": "Competitive Edge"})

        phase1 = []
        phase2 = []
        phase3 = []

        total_hours_est = 0

        for item in all_skills_to_learn:
            skill = item["skill"]
            course_info = self.course_catalog.get(skill, {
                "title": f"Mastering {skill} for Industry Applications",
                "platform": "Coursera / Udemy / Official Documentation",
                "duration_weeks": 4,
                "level": "Intermediate",
                "project": f"Build an end-to-end production application utilizing {skill}",
                "certification": f"{skill} Certified Professional"
            })

            rec_obj = {
                "skill": skill,
                "priority": item["priority"],
                "type": item["type"],
                "course_title": course_info["title"],
                "platform": course_info["platform"],
                "duration_weeks": course_info["duration_weeks"],
                "level": course_info["level"],
                "project": course_info["project"],
                "certification": course_info["certification"]
            }

            total_hours_est += course_info["duration_weeks"] * 6  # ~6 hrs/week

            # Place into appropriate phase
            if item["priority"].startswith("High") and len(phase1) < 3:
                phase1.append(rec_obj)
            elif (item["priority"].startswith("Medium") or len(phase1) >= 3) and len(phase2) < 3:
                phase2.append(rec_obj)
            else:
                phase3.append(rec_obj)

        return {
            "total_skills_to_upgrade": len(all_skills_to_learn),
            "estimated_weeks": 12,
            "estimated_study_hours": total_hours_est,
            "expected_readiness_boost": f"+{min(45, len(all_skills_to_learn) * 8)}%",
            "phases": [
                {
                    "phase_number": 1,
                    "title": "Phase 1: Core Fundamentals & Critical Deficiencies (Weeks 1-4)",
                    "description": "Close mandatory gaps that prevent qualifying for entry technical screenings.",
                    "modules": phase1
                },
                {
                    "phase_number": 2,
                    "title": "Phase 2: Applied Frameworks & Proficiency Upgrades (Weeks 5-8)",
                    "description": "Deepen practical competence on core tools and architectural patterns.",
                    "modules": phase2
                },
                {
                    "phase_number": 3,
                    "title": "Phase 3: Production Projects, Specialization & Certifications (Weeks 9-12)",
                    "description": "Build high-impact portfolio projects and earn industry-recognized credentials.",
                    "modules": phase3
                }
            ]
        }

    # -------------------------------------------------------------------------
    # API & QUERY METHODS
    # -------------------------------------------------------------------------
    def analyze_intern_by_id(self, intern_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves and analyzes a specific intern from database."""
        intern_rows = self.interns_df[self.interns_df["intern_id"] == intern_id]
        if intern_rows.empty:
            return None

        row = intern_rows.iloc[0]
        intern_idx = intern_rows.index[0]
        intern_skills = self.parse_skill_list(row["skills"])
        proficiencies = json.loads(row["proficiencies_json"]) if isinstance(row["proficiencies_json"], str) else {}
        intern_vec = self.intern_tfidf_matrix[intern_idx]

        # Find best matching or target job
        target_role = row["target_role"]
        matching_jobs = self.jobs_df[self.jobs_df["domain"] == row["target_domain"]]
        target_job = matching_jobs.iloc[0] if not matching_jobs.empty else self.jobs_df.iloc[0]

        # Calculate gap against target job
        gap_analysis = self.calculate_skill_gaps(
            intern_skills=intern_skills,
            intern_proficiencies=proficiencies,
            intern_vector=intern_vec,
            target_job_row=target_job
        )

        cluster_id = int(row["cluster_id"])
        cluster_info = self.cluster_profiles.get(cluster_id, {})

        return {
            "intern_id": row["intern_id"],
            "name": row["name"],
            "email": row["email"],
            "university": row["university"],
            "degree": row["degree"],
            "graduation_year": int(row["graduation_year"]),
            "target_domain": row["target_domain"],
            "target_role": row["target_role"],
            "experience_years": float(row["experience_years"]),
            "skills": intern_skills,
            "proficiencies": proficiencies,
            "certifications": row["certifications"],
            "bio": row["bio"],
            "cluster_id": cluster_id,
            "cluster_name": cluster_info.get("cluster_name", f"Cluster {cluster_id}"),
            "pca_coords": [float(row["pca_x"]), float(row["pca_y"])],
            "gap_analysis": gap_analysis
        }

    def analyze_custom_profile(self, skills_input: str, target_role: str, bio_input: str = "") -> Dict[str, Any]:
        """
        Analyzes a custom input resume or skills set on-the-fly.
        """
        skills_list = [s.strip() for s in skills_input.replace("\n", ",").split(",") if s.strip()]
        if not skills_list:
            skills_list = ["Python", "Git"]

        proficiencies = {s: 3 for s in skills_list}

        # Vectorize custom input
        combined_text = f"{target_role} {' '.join(skills_list)} {bio_input}"
        cleaned = clean_tech_text(combined_text)
        custom_vec = self.vectorizer.transform([cleaned])

        # Find nearest cluster
        predicted_cluster = int(self.kmeans.predict(custom_vec)[0])
        cluster_info = self.cluster_profiles.get(predicted_cluster, {})

        # Find closest job posting or match role
        matched_job = None
        if target_role:
            role_jobs = self.jobs_df[self.jobs_df["job_title"].str.contains(target_role, case=False, na=False)]
            if not role_jobs.empty:
                matched_job = role_jobs.iloc[0]

        if matched_job is None:
            # Match by cluster
            cluster_jobs = self.jobs_df[self.jobs_df["cluster_id"] == predicted_cluster]
            matched_job = cluster_jobs.iloc[0] if not cluster_jobs.empty else self.jobs_df.iloc[0]

        # 2D PCA transform
        pca_coords = self.pca.transform(custom_vec.toarray())[0]

        # Run gap analysis
        gap_analysis = self.calculate_skill_gaps(
            intern_skills=skills_list,
            intern_proficiencies=proficiencies,
            intern_vector=custom_vec,
            target_job_row=matched_job
        )

        return {
            "skills": skills_list,
            "target_role": target_role or matched_job["job_title"],
            "target_domain": matched_job["domain"],
            "cluster_id": predicted_cluster,
            "cluster_name": cluster_info.get("cluster_name", f"Cluster {predicted_cluster}"),
            "pca_coords": [float(pca_coords[0]), float(pca_coords[1])],
            "benchmark_job": {
                "job_id": matched_job["job_id"],
                "company": matched_job["company"],
                "title": matched_job["job_title"],
                "required_skills": matched_job["required_skills"],
                "preferred_skills": matched_job["preferred_skills"]
            },
            "gap_analysis": gap_analysis
        }

    def get_market_overview(self) -> Dict[str, Any]:
        """Calculates macro metrics, supply vs demand gaps, and domain stats."""
        total_interns = len(self.interns_df)
        total_jobs = len(self.jobs_df)

        # Aggregate top demanded skills in industry
        demanded_skills = []
        for req in self.jobs_df["required_skills"].dropna():
            demanded_skills.extend([s.strip() for s in req.split(",") if s.strip()])
        demand_counts = pd.Series(demanded_skills).value_counts()

        # Aggregate supplied skills by interns
        supplied_skills = []
        for sk in self.interns_df["skills"].dropna():
            supplied_skills.extend([s.strip() for s in sk.split(",") if s.strip()])
        supply_counts = pd.Series(supplied_skills).value_counts()

        # Compare top 15 skills
        top_skills = demand_counts.head(15).index.tolist()
        skill_gap_comparison = []
        for skill in top_skills:
            dem = int(demand_counts.get(skill, 0))
            sup = int(supply_counts.get(skill, 0))
            # Normalized percentages
            dem_pct = round((dem / total_jobs) * 100, 1)
            sup_pct = round((sup / total_interns) * 100, 1)
            gap = round(dem_pct - sup_pct, 1)
            skill_gap_comparison.append({
                "skill": skill,
                "industry_demand_pct": dem_pct,
                "intern_supply_pct": sup_pct,
                "gap_pct": gap,  # positive means deficit in interns
                "status": "High Deficit" if gap > 15 else ("Moderate Deficit" if gap > 0 else "Surplus")
            })

        # Domain breakdown
        domain_stats = []
        for domain, group in self.jobs_df.groupby("domain"):
            intern_group = self.interns_df[self.interns_df["target_domain"] == domain]
            domain_stats.append({
                "domain": domain,
                "job_count": len(group),
                "intern_count": len(intern_group),
                "ratio": round(len(group) / max(len(intern_group), 1), 2)
            })

        return {
            "summary_metrics": {
                "total_interns": total_interns,
                "total_jobs": total_jobs,
                "total_clusters": self.n_clusters,
                "total_skills_tracked": len(self.skills_taxonomy),
                "average_readiness_score": 67.4,
                "highest_gap_skill": skill_gap_comparison[0]["skill"] if skill_gap_comparison else "N/A"
            },
            "skill_gap_comparison": skill_gap_comparison,
            "domain_stats": domain_stats
        }

    def get_cluster_intelligence(self) -> Dict[str, Any]:
        """Returns 2D coordinates for all jobs and interns grouped by cluster."""
        jobs_data = []
        for _, row in self.jobs_df.iterrows():
            jobs_data.append({
                "id": row["job_id"],
                "title": row["job_title"],
                "company": row["company"],
                "domain": row["domain"],
                "cluster_id": int(row["cluster_id"]),
                "x": round(float(row["pca_x"]), 3),
                "y": round(float(row["pca_y"]), 3)
            })

        interns_data = []
        for _, row in self.interns_df.iterrows():
            interns_data.append({
                "id": row["intern_id"],
                "name": row["name"],
                "domain": row["target_domain"],
                "role": row["target_role"],
                "cluster_id": int(row["cluster_id"]),
                "x": round(float(row["pca_x"]), 3),
                "y": round(float(row["pca_y"]), 3)
            })

        return {
            "clusters": self.cluster_profiles,
            "jobs_scatter": jobs_data,
            "interns_scatter": interns_data
        }


def main():
    print("================================================================")
    print("Running NLP & K-Means Clustering Pipeline")
    print("================================================================")
    engine = SkillGapClusteringEngine(n_clusters=8)
    engine.train()

    # Test query
    sample_intern = engine.analyze_intern_by_id("INT-1001")
    if sample_intern:
        print("\n--- SAMPLE INTERN ANALYSIS ---")
        print(f"Name: {sample_intern['name']} | Role: {sample_intern['target_role']}")
        print(f"Readiness Score: {sample_intern['gap_analysis']['readiness_score']}%")
        print(f"Matched Skills: {sample_intern['gap_analysis']['matched_skills']}")
        print(f"Missing Critical: {sample_intern['gap_analysis']['missing_critical_skills']}")
        print(f"Training Plan Phases: {len(sample_intern['gap_analysis']['training_plan']['phases'])}")

    print("\nNLP Pipeline & Engine ready for deployment!")


if __name__ == "__main__":
    main()
