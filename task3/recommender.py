#!/usr/bin/env python3
"""
Internship AI Recommendation Engine & Roadmap Generator
======================================================
Core recommendation library featuring:
- Matrix Factorization Collaborative Filtering (Funk SVD with User/Item Biases)
- Cold-Start Recommender for brand new students with zero rating history
- Prerequisite Dependency Resolver & Topological DAG Scheduler
- Multi-Level Roadmap Generator (Beginner -> Intermediate -> Advanced)
"""

import math
import random
import csv
from datetime import datetime
from pathlib import Path
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Set, Optional, Any


class DataLoader:
    """Loads and preprocesses datasets for courses, interns, prerequisites, and ratings."""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.courses: Dict[str, Dict[str, Any]] = {}
        self.interns: Dict[str, Dict[str, Any]] = {}
        self.prerequisites: Dict[str, str] = {}  # target_course_id -> prereq_course_id
        self.prereq_rules: List[Dict[str, Any]] = []
        self.ratings_data: List[Dict[str, Any]] = []
        self.user_rated_courses: Dict[str, Set[str]] = defaultdict(set)
        self.user_completed_courses: Dict[str, Set[str]] = defaultdict(set)
        
        self.load_all()

    def load_all(self):
        """Load all CSV files from data directory."""
        # 1. Courses
        courses_file = self.data_dir / "courses.csv"
        if not courses_file.exists():
            raise FileNotFoundError(f"Missing {courses_file}. Please run generate_data.py first.")
        with open(courses_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                row["duration_weeks"] = int(row["duration_weeks"])
                row["credit_units"] = int(row["credit_units"])
                self.courses[row["course_id"]] = row

        # 2. Prerequisite Rules
        prereq_file = self.data_dir / "prerequisite_rules.csv"
        if prereq_file.exists():
            with open(prereq_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.prereq_rules.append(row)
                    self.prerequisites[row["target_course_id"]] = row["prerequisite_course_id"]

        # 3. Interns
        interns_file = self.data_dir / "interns.csv"
        if interns_file.exists():
            with open(interns_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.interns[row["intern_id"]] = row

        # 4. Ratings and Completions
        ratings_file = self.data_dir / "ratings_and_completions.csv"
        if ratings_file.exists():
            with open(ratings_file, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    intern_id = row["intern_id"]
                    course_id = row["course_id"]
                    status = row["completion_status"]
                    rating_str = row["rating"].strip()
                    
                    if status == "Completed":
                        self.user_completed_courses[intern_id].add(course_id)

                    if rating_str != "":
                        rating_val = float(rating_str)
                        self.ratings_data.append({
                            "intern_id": intern_id,
                            "course_id": course_id,
                            "rating": rating_val,
                            "completion_status": status,
                            "progress_percent": int(row.get("progress_percent", 0) or 0),
                        })
                        self.user_rated_courses[intern_id].add(course_id)


class MatrixFactorizationSVD:
    """
    Bias-Augmented Matrix Factorization (SVD) for Collaborative Filtering.
    Prediction model: r_hat(u, i) = mu + b_u + b_i + p_u . q_i
    Optimized with Stochastic Gradient Descent (SGD) with L2 regularization.
    """

    def __init__(self, n_factors: int = 16, lr: float = 0.008, reg: float = 0.04, n_epochs: int = 25, seed: int = 42):
        self.n_factors = n_factors
        self.lr = lr
        self.reg = reg
        self.n_epochs = n_epochs
        self.seed = seed

        self.global_mean: float = 3.5
        self.user_biases: Dict[str, float] = defaultdict(float)
        self.item_biases: Dict[str, float] = defaultdict(float)
        self.user_factors: Dict[str, List[float]] = {}
        self.item_factors: Dict[str, List[float]] = {}
        self.users: List[str] = []
        self.items: List[str] = []

    def fit(self, ratings: List[Dict[str, Any]], verbose: bool = False):
        """Fit the matrix factorization model using SGD."""
        random.seed(self.seed)
        
        # Calculate global mean
        total_rating = sum(r["rating"] for r in ratings)
        self.global_mean = total_rating / len(ratings) if ratings else 3.5

        # Initialize users and items
        unique_users = sorted(list({r["intern_id"] for r in ratings}))
        unique_items = sorted(list({r["course_id"] for r in ratings}))
        self.users = unique_users
        self.items = unique_items

        # Initialize biases to 0
        self.user_biases = {u: 0.0 for u in unique_users}
        self.item_biases = {i: 0.0 for i in unique_items}

        # Initialize latent factor vectors with small random normal values (std = 0.05)
        self.user_factors = {
            u: [random.gauss(0, 0.05) for _ in range(self.n_factors)]
            for u in unique_users
        }
        self.item_factors = {
            i: [random.gauss(0, 0.05) for _ in range(self.n_factors)]
            for i in unique_items
        }

        # SGD Training Loop
        for epoch in range(1, self.n_epochs + 1):
            random.shuffle(ratings)
            loss = 0.0
            
            for entry in ratings:
                u = entry["intern_id"]
                i = entry["course_id"]
                r = entry["rating"]

                p_u = self.user_factors[u]
                q_i = self.item_factors[i]
                b_u = self.user_biases[u]
                b_i = self.item_biases[i]

                # Dot product
                dot = sum(p_u[f] * q_i[f] for f in range(self.n_factors))
                pred = self.global_mean + b_u + b_i + dot

                # Error
                err = r - pred
                loss += err ** 2

                # Update biases
                self.user_biases[u] += self.lr * (err - self.reg * b_u)
                self.item_biases[i] += self.lr * (err - self.reg * b_i)

                # Update latent factors
                for f in range(self.n_factors):
                    p_uf = p_u[f]
                    q_if = q_i[f]
                    p_u[f] += self.lr * (err * q_if - self.reg * p_uf)
                    q_i[f] += self.lr * (err * p_uf - self.reg * q_if)

            if verbose and (epoch % 5 == 0 or epoch == self.n_epochs):
                rmse = math.sqrt(loss / len(ratings))
                print(f"  Epoch {epoch:2d}/{self.n_epochs} - Train RMSE: {rmse:.4f}")

    def predict(self, user_id: str, item_id: str) -> float:
        """Predict rating for a given user and course."""
        b_u = self.user_biases.get(user_id, 0.0)
        b_i = self.item_biases.get(item_id, 0.0)

        if user_id in self.user_factors and item_id in self.item_factors:
            p_u = self.user_factors[user_id]
            q_i = self.item_factors[item_id]
            dot = sum(p_u[f] * q_i[f] for f in range(self.n_factors))
        else:
            dot = 0.0

        est = self.global_mean + b_u + b_i + dot
        # Clip to valid 1-5 rating range
        return max(1.0, min(5.0, est))

    def evaluate(self, test_ratings: List[Dict[str, Any]]) -> Dict[str, float]:
        """Evaluate model on a test set (returns RMSE and MAE)."""
        if not test_ratings:
            return {"rmse": 0.0, "mae": 0.0, "count": 0}

        sq_err_sum = 0.0
        abs_err_sum = 0.0

        for entry in test_ratings:
            pred = self.predict(entry["intern_id"], entry["course_id"])
            actual = entry["rating"]
            err = actual - pred
            sq_err_sum += err ** 2
            abs_err_sum += abs(err)

        n = len(test_ratings)
        rmse = math.sqrt(sq_err_sum / n)
        mae = abs_err_sum / n

        return {
            "rmse": round(rmse, 4),
            "mae": round(mae, 4),
            "count": n
        }


class ColdStartEngine:
    """
    Cold-Start Recommender for brand new students with no historical ratings.
    Combines:
    - Career Field Track Relevance prior
    - Bayesian Average Course Quality Rating
    - Completion Rate & Popularity
    - Foundational Starter Readiness Score
    """

    def __init__(self, data_loader: DataLoader):
        self.dl = data_loader
        self.course_stats: Dict[str, Dict[str, Any]] = {}
        self._compute_course_statistics()

    def _compute_course_statistics(self):
        """Compute Bayesian average rating, completion rate, and popularity for all courses."""
        ratings_by_course = defaultdict(list)
        completions_by_course = defaultdict(int)
        enrollments_by_course = defaultdict(int)

        for r in self.dl.ratings_data:
            c_id = r["course_id"]
            ratings_by_course[c_id].append(r["rating"])
            enrollments_by_course[c_id] += 1
            if r["completion_status"] == "Completed":
                completions_by_course[c_id] += 1

        # Global average rating (C) and confidence weight (m)
        all_ratings = [r["rating"] for r in self.dl.ratings_data]
        global_avg_rating = sum(all_ratings) / len(all_ratings) if all_ratings else 3.8
        m_weight = 10  # smoothing prior weight

        for c_id, course in self.dl.courses.items():
            r_list = ratings_by_course[c_id]
            v = len(r_list)
            r_avg = sum(r_list) / v if v > 0 else global_avg_rating
            
            # Bayesian smoothed rating: (v / (v + m)) * R + (m / (v + m)) * C
            bayesian_rating = (v / (v + m_weight)) * r_avg + (m_weight / (v + m_weight)) * global_avg_rating

            comp_count = completions_by_course[c_id]
            enr_count = enrollments_by_course[c_id]
            completion_rate = (comp_count / enr_count) if enr_count > 0 else 0.80

            self.course_stats[c_id] = {
                "avg_rating": round(r_avg, 2),
                "bayesian_rating": round(bayesian_rating, 3),
                "review_count": v,
                "completion_rate": round(completion_rate, 3),
                "popularity_score": v,
            }

    def score_for_new_student(
        self,
        course_id: str,
        target_career_field: Optional[str] = None,
        education_level: Optional[str] = None
    ) -> Tuple[float, str]:
        """
        Calculate composite recommendation score for a new student.
        Returns: (predicted_score, reason_explanation)
        """
        course = self.dl.courses[course_id]
        stats = self.course_stats.get(course_id, {
            "bayesian_rating": 4.0, "completion_rate": 0.85, "review_count": 0
        })

        base_score = stats["bayesian_rating"]
        reasons = []

        # 1. Career Track Affinity Boost
        if target_career_field and course["career_field"].lower() == target_career_field.lower():
            base_score += 0.65
            reasons.append(f"Direct match for '{course['career_field']}'")
        elif target_career_field:
            # Related field synergy
            base_score += 0.05

        # 2. Difficulty Starter Alignment (for new interns, Beginner courses get higher starter priority)
        diff = course["difficulty_level"]
        if diff == "Beginner":
            base_score += 0.35
            reasons.append("Essential foundation course")
        elif diff == "Intermediate":
            base_score += 0.15
        elif diff == "Advanced":
            base_score -= 0.10  # Slight penalty for initial cold-start listing

        # 3. High Completion & Student Satisfaction Boost
        if stats["completion_rate"] >= 0.80:
            base_score += 0.10
            reasons.append(f"High student completion rate ({stats['completion_rate']*100:.0f}%)")

        reason_str = "; ".join(reasons) if reasons else f"Overall quality score ({stats['bayesian_rating']} ★)"
        # Bound score between 1.0 and 5.0
        final_score = max(1.0, min(5.0, base_score))
        return round(final_score, 2), reason_str


class RoadmapGenerator:
    """
    Constructs a topological, multi-phase learning roadmap.
    Enforces:
    1. Prerequisite Closure (Dependency Injection)
    2. Strict Level Partitioning (Beginner -> Intermediate -> Advanced)
    3. Topological Sort (Prerequisites always precede target courses)
    """

    def __init__(self, data_loader: DataLoader):
        self.dl = data_loader

    def build_roadmap(
        self,
        candidate_courses_with_scores: List[Tuple[str, float, str]],
        completed_course_ids: Set[str],
        max_courses: int = 9,
    ) -> Dict[str, Any]:
        """
        Build a step-by-step roadmap from scored candidate courses.
        
        Args:
            candidate_courses_with_scores: List of (course_id, score, reason)
            completed_course_ids: Set of courses the student has already finished
            max_courses: Desired roadmap length (default: 8-10)

        Returns:
            Structured dictionary containing roadmap metadata, levels, and ordered steps.
        """
        # Map course_id to score and reason
        score_map = {c_id: score for c_id, score, _ in candidate_courses_with_scores}
        reason_map = {c_id: reason for c_id, score, reason in candidate_courses_with_scores}

        # Step 1: Filter out already completed courses
        filtered_candidates = [
            (c_id, score, reason)
            for c_id, score, reason in candidate_courses_with_scores
            if c_id not in completed_course_ids
        ]

        # Step 2: Select Top Courses
        selected_set: Set[str] = set()
        for c_id, _, _ in filtered_candidates:
            if len(selected_set) >= max_courses:
                break
            selected_set.add(c_id)

        # Step 3: Prerequisite Dependency Injection (Closure)
        # If any selected course requires a prerequisite that the student has NOT completed,
        # we MUST inject the prerequisite into selected_set!
        injected_prereqs = []
        for target_id in list(selected_set):
            if target_id in self.dl.prerequisites:
                prereq_id = self.dl.prerequisites[target_id]
                if prereq_id not in completed_course_ids and prereq_id not in selected_set:
                    selected_set.add(prereq_id)
                    target_title = self.dl.courses[target_id]["course_title"]
                    prereq_reason = f"Required prerequisite for '{target_title}'"
                    reason_map[prereq_id] = prereq_reason
                    score_map[prereq_id] = max(score_map.get(prereq_id, 4.0), score_map.get(target_id, 4.0))
                    injected_prereqs.append(prereq_id)

        # Step 4: Partition into Difficulty Levels
        # Levels: Beginner (1), Intermediate (2), Advanced (3)
        level_order = {"Beginner": 1, "Intermediate": 2, "Advanced": 3}
        courses_by_level = {
            "Beginner": [],
            "Intermediate": [],
            "Advanced": [],
        }

        for c_id in selected_set:
            course = self.dl.courses[c_id]
            diff = course["difficulty_level"]
            courses_by_level[diff].append(c_id)

        # Step 5: Topological Sort within and across levels
        # Build dependency graph
        # graph[u] = list of courses that depend on u
        graph = defaultdict(list)
        in_degree = defaultdict(int)

        for c_id in selected_set:
            in_degree[c_id] = 0

        for target_id in selected_set:
            if target_id in self.dl.prerequisites:
                prereq_id = self.dl.prerequisites[target_id]
                if prereq_id in selected_set:
                    graph[prereq_id].append(target_id)
                    in_degree[target_id] += 1

        # Order courses: Beginner -> Intermediate -> Advanced, respecting DAG
        ordered_course_ids: List[str] = []
        
        # Sort each level by score (descending)
        for diff in ["Beginner", "Intermediate", "Advanced"]:
            level_courses = sorted(
                courses_by_level[diff],
                key=lambda x: (in_degree[x], -score_map.get(x, 0.0))
            )
            
            # Sub-topological sort for this level
            queue = deque([c for c in level_courses if in_degree[c] == 0])
            level_resolved = []
            
            while queue:
                curr = queue.popleft()
                level_resolved.append(curr)
                for neighbor in graph[curr]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0 and neighbor in courses_by_level[diff]:
                        queue.append(neighbor)

            # In case of any remaining in this level
            for c in level_courses:
                if c not in level_resolved:
                    level_resolved.append(c)

            ordered_course_ids.extend(level_resolved)

        # Step 6: Construct Step-by-Step Structured Roadmap
        roadmap_phases = []
        current_step = 1
        total_weeks = 0
        total_credits = 0

        phase_titles = {
            "Beginner": {
                "phase_name": "Phase 1: Foundational Core",
                "badge": "🟢 BEGINNER",
                "description": "Essential concepts, core toolchains, and foundational theory."
            },
            "Intermediate": {
                "phase_name": "Phase 2: Professional Development & Architecture",
                "badge": "🟡 INTERMEDIATE",
                "description": "Applied industry patterns, framework mastery, and scalable engineering."
            },
            "Advanced": {
                "phase_name": "Phase 3: Specialization, Mastery & Leadership",
                "badge": "🔴 ADVANCED",
                "description": "Distributed systems, production deployment, and cutting-edge paradigms."
            }
        }

        for diff in ["Beginner", "Intermediate", "Advanced"]:
            phase_course_ids = [cid for cid in ordered_course_ids if self.dl.courses[cid]["difficulty_level"] == diff]
            if not phase_course_ids:
                continue

            phase_info = phase_titles[diff]
            phase_steps = []
            phase_weeks = 0
            phase_credits = 0

            for cid in phase_course_ids:
                c_data = self.dl.courses[cid]
                pred_score = score_map.get(cid, 4.0)
                reason = reason_map.get(cid, "Recommended based on curriculum affinity")
                prereq_id = self.dl.prerequisites.get(cid)
                prereq_title = self.dl.courses[prereq_id]["course_title"] if prereq_id else None

                step_data = {
                    "step_number": current_step,
                    "course_id": cid,
                    "course_title": c_data["course_title"],
                    "career_field": c_data["career_field"],
                    "difficulty_level": diff,
                    "duration_weeks": c_data["duration_weeks"],
                    "credit_units": c_data["credit_units"],
                    "predicted_rating": round(pred_score, 2),
                    "recommendation_reason": reason,
                    "prerequisite_course_id": prereq_id,
                    "prerequisite_course_title": prereq_title,
                    "description": c_data["description"],
                    "is_injected_prereq": cid in injected_prereqs,
                }
                phase_steps.append(step_data)
                phase_weeks += c_data["duration_weeks"]
                phase_credits += c_data["credit_units"]
                current_step += 1

            total_weeks += phase_weeks
            total_credits += phase_credits

            roadmap_phases.append({
                "phase_id": diff.lower(),
                "phase_title": phase_info["phase_name"],
                "phase_badge": phase_info["badge"],
                "phase_description": phase_info["description"],
                "difficulty_level": diff,
                "total_weeks": phase_weeks,
                "total_credits": phase_credits,
                "steps": phase_steps,
            })

        return {
            "total_courses": len(ordered_course_ids),
            "total_estimated_weeks": total_weeks,
            "total_credit_units": total_credits,
            "injected_prerequisites_count": len(injected_prereqs),
            "phases": roadmap_phases,
        }


class InternshipRecommender:
    """
    Unified AI Recommendation Engine.
    Coordinates Collaborative Filtering, Cold-Start, and Roadmap generation.
    """

    def __init__(self, data_dir: str = "data", seed: int = 42):
        self.dl = DataLoader(data_dir=data_dir)
        self.cf_model = MatrixFactorizationSVD(n_factors=16, lr=0.008, reg=0.04, n_epochs=25, seed=seed)
        self.cold_start = ColdStartEngine(self.dl)
        self.roadmap_gen = RoadmapGenerator(self.dl)
        self.is_trained = False

    def train(self, verbose: bool = False) -> Dict[str, Any]:
        """Train the collaborative filtering model and evaluate on an 80/20 train/test split."""
        # 80/20 train/test split
        random.seed(42)
        ratings_shuffled = list(self.dl.ratings_data)
        random.shuffle(ratings_shuffled)
        
        split_idx = int(len(ratings_shuffled) * 0.80)
        train_ratings = ratings_shuffled[:split_idx]
        test_ratings = ratings_shuffled[split_idx:]

        if verbose:
            print(f"Training SVD Collaborative Filtering Model on {len(train_ratings):,} ratings...")

        self.cf_model.fit(train_ratings, verbose=verbose)
        self.is_trained = True

        eval_metrics = self.cf_model.evaluate(test_ratings)
        if verbose:
            print(f"Evaluation on {len(test_ratings):,} test ratings:")
            print(f"  - RMSE: {eval_metrics['rmse']:.4f}")
            print(f"  - MAE:  {eval_metrics['mae']:.4f}")

        # Retrain on full dataset for maximum inference power
        self.cf_model.fit(self.dl.ratings_data, verbose=False)
        return eval_metrics

    def recommend_for_intern(
        self,
        intern_id: str,
        target_career_field: Optional[str] = None,
        roadmap_size: int = 9
    ) -> Dict[str, Any]:
        """
        Generate a personalized step-by-step learning roadmap for an existing intern.
        """
        if not self.is_trained:
            self.train(verbose=False)

        intern_profile = self.dl.interns.get(intern_id)
        if not intern_profile:
            raise ValueError(f"Intern ID '{intern_id}' not found in database.")

        field = target_career_field or intern_profile["primary_career_field"]
        completed = self.dl.user_completed_courses.get(intern_id, set())

        # Check if intern has rating history
        rated_courses = self.dl.user_rated_courses.get(intern_id, set())

        candidate_scores = []
        for course_id, course in self.dl.courses.items():
            if course_id in completed:
                continue

            if len(rated_courses) > 0:
                # Use Collaborative Filtering SVD
                pred_rating = self.cf_model.predict(intern_id, course_id)
                # Boost if matches target field
                if course["career_field"].lower() == field.lower():
                    pred_rating += 0.30
                reason = f"Predicted affinity {pred_rating:.2f} ★ (Collaborative Filtering)"
                if course["career_field"].lower() == field.lower():
                    reason += f" & matches '{field}' track"
            else:
                # Fallback to cold start for this intern
                pred_rating, reason = self.cold_start.score_for_new_student(
                    course_id=course_id,
                    target_career_field=field,
                    education_level=intern_profile.get("education_level")
                )

            candidate_scores.append((course_id, pred_rating, reason))

        # Sort by predicted score descending
        candidate_scores.sort(key=lambda x: x[1], reverse=True)

        # Build Roadmap
        roadmap = self.roadmap_gen.build_roadmap(
            candidate_courses_with_scores=candidate_scores,
            completed_course_ids=completed,
            max_courses=roadmap_size,
        )

        return {
            "mode": "existing_intern",
            "intern_id": intern_id,
            "intern_name": f"{intern_profile['first_name']} {intern_profile['last_name']}",
            "education_level": intern_profile["education_level"],
            "academic_major": intern_profile["academic_major"],
            "career_field": field,
            "past_courses_completed_count": len(completed),
            "past_completed_course_ids": sorted(list(completed)),
            "roadmap": roadmap,
        }

    def recommend_for_new_student(
        self,
        student_name: str = "New Intern",
        target_career_field: str = "Web & Full-Stack Development",
        education_level: str = "Undergraduate Student",
        academic_major: str = "Computer Science",
        roadmap_size: int = 9
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive, step-by-step roadmap for a brand-new student with ZERO history.
        Uses the Cold-Start Recommender Engine.
        """
        if not self.is_trained:
            self.train(verbose=False)

        candidate_scores = []
        for course_id in self.dl.courses:
            score, reason = self.cold_start.score_for_new_student(
                course_id=course_id,
                target_career_field=target_career_field,
                education_level=education_level
            )
            candidate_scores.append((course_id, score, reason))

        candidate_scores.sort(key=lambda x: x[1], reverse=True)

        roadmap = self.roadmap_gen.build_roadmap(
            candidate_courses_with_scores=candidate_scores,
            completed_course_ids=set(),
            max_courses=roadmap_size,
        )

        return {
            "mode": "new_student_cold_start",
            "intern_name": student_name,
            "education_level": education_level,
            "academic_major": academic_major,
            "career_field": target_career_field,
            "past_courses_completed_count": 0,
            "past_completed_course_ids": [],
            "roadmap": roadmap,
        }
