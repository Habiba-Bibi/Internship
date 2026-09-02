import os
import json
import re
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class InternshipNLPMatcher:
    def __init__(self, faqs_path: str, tickets_path: str):
        self.faqs_path = faqs_path
        self.tickets_path = tickets_path
        self.faqs: List[Dict[str, Any]] = []
        self.tickets: List[Dict[str, Any]] = []
        
        # Corpus documents for vectorizer
        self.corpus_docs: List[str] = []
        self.corpus_meta: List[Dict[str, Any]] = []
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        
        # Category definitions
        self.categories = [
            "Weekly Tasks & Submissions",
            "GitHub & Version Control",
            "Deadlines & Extensions",
            "Grading & Evaluations",
            "Certificates & Program Completion",
            "Mentorship & Office Hours",
            "Environment & Dependencies",
            "Backend & API",
            "Frontend & UI",
            "Authentication & Security"
        ]
        
        self.load_data()
        self.build_index()

    def load_data(self):
        """Loads FAQs and Historical Support Tickets from JSON datasets."""
        if os.path.exists(self.faqs_path):
            with open(self.faqs_path, "r", encoding="utf-8") as f:
                self.faqs = json.load(f)
        else:
            self.faqs = []

        if os.path.exists(self.tickets_path):
            with open(self.tickets_path, "r", encoding="utf-8") as f:
                self.tickets = json.load(f)
        else:
            self.tickets = []

    def _normalize_text(self, text: str) -> str:
        """Cleans and standardizes text for semantic embedding."""
        if not text:
            return ""
        # Lowercase and clean special chars while preserving tech tokens
        text = text.lower()
        # Keep dashes and dots in technical terms (like node.js, ci/cd, --legacy-peer-deps)
        text = re.sub(r"[^\w\s\-\.\/]", " ", text)
        return " ".join(text.split())

    def build_index(self):
        """Builds weighted semantic document index across FAQs and Historical Tickets."""
        self.corpus_docs = []
        self.corpus_meta = []

        # Index FAQs
        for faq in self.faqs:
            # Combine question, sample queries, keywords, and answer for deep indexing
            sample_q = " ".join(faq.get("sample_queries", []))
            keywords = " ".join(faq.get("keywords", []))
            q_text = faq.get("question", "")
            cat = faq.get("category", "")
            ans = faq.get("answer", "")
            
            # Form weighted combined text (questions & sample queries repeated for higher weight)
            combined_text = f"{q_text} {q_text} {sample_q} {sample_q} {keywords} {keywords} {cat} {ans}"
            self.corpus_docs.append(self._normalize_text(combined_text))
            self.corpus_meta.append({
                "type": "FAQ",
                "id": faq.get("id"),
                "title": q_text,
                "category": cat,
                "data": faq
            })

        # Index Historical Tickets
        for ticket in self.tickets:
            title = ticket.get("title", "")
            desc = ticket.get("description", "")
            error_log = ticket.get("error_log", "")
            root_cause = ticket.get("root_cause", "")
            solution = ticket.get("solution_steps", "")
            tags = " ".join(ticket.get("tags", []))
            cat = ticket.get("category", "")
            
            # Form weighted document
            combined_text = f"{title} {title} {desc} {error_log} {root_cause} {solution} {tags} {tags} {cat}"
            self.corpus_docs.append(self._normalize_text(combined_text))
            self.corpus_meta.append({
                "type": "TICKET",
                "id": ticket.get("id") or ticket.get("ticket_number"),
                "title": title,
                "category": cat,
                "data": ticket
            })

        # Train TF-IDF vectorizer with unigram + bigram semantic representations
        if self.corpus_docs:
            self.vectorizer = TfidfVectorizer(
                ngram_range=(1, 3),
                sublinear_tf=True,
                max_features=5000,
                token_pattern=r"(?u)\b\w[\w\-\.]+\b"
            )
            self.tfidf_matrix = self.vectorizer.fit_transform(self.corpus_docs)

    def classify_category(self, query: str) -> Tuple[str, float]:
        """Classifies the intern query into an internship domain category."""
        norm_q = query.lower()
        
        category_keywords = {
            "Weekly Tasks & Submissions": ["task", "submission", "submit", "assignment", "loom", "video", "pr link", "portal", "milestone", "capstone"],
            "GitHub & Version Control": ["git", "github", "branch", "commit", "push", "pull request", "pr", "rebase", "merge conflict", "remote", "ssh", "lfs", "actions", "repo", "fork", "upstream"],
            "Deadlines & Extensions": ["deadline", "due date", "late", "extension", "grace period", "penalty", "due time", "emergency", "power outage", "extra time", "delay"],
            "Grading & Evaluations": ["grade", "grading", "score", "rubric", "points", "marks", "resubmit", "re-evaluation", "review", "feedback", "evaluation", "pass"],
            "Certificates & Program Completion": ["certificate", "completion", "credly", "badge", "lor", "letter of recommendation", "graduate", "verification letter", "accredited", "linkedin"],
            "Mentorship & Office Hours": ["mentor", "office hour", "1-on-1", "calendly", "call", "slack", "discord", "doubt", "ask question", "help", "sla", "session"],
            "Environment & Dependencies": ["python", "node", "install", "pip", "npm", "virtualenv", "venv", "docker", "port", "environment", "setup", "requirements", "modulenotfounderror"],
            "Backend & API": ["fastapi", "uvicorn", "cors", "pydantic", "api", "422", "endpoint", "backend", "database", "sqlite", "rate limit", "429"],
            "Frontend & UI": ["react", "vite", "jsx", "tsx", "useeffect", "frontend", "ui", "component", "css", "lucide", "infinite loop"],
            "Authentication & Security": ["jwt", "token", "401", "unauthorized", "secret", "api key", "auth", "login", "password", "security", ".env"]
        }
        
        scores = {}
        for cat, kw_list in category_keywords.items():
            count = sum(1 for kw in kw_list if kw in norm_q)
            if count > 0:
                scores[cat] = count
                
        if scores:
            best_cat = max(scores, key=scores.get)
            confidence = min(0.95, 0.45 + (scores[best_cat] * 0.15))
            return best_cat, round(confidence, 2)
            
        return "General Internship Support", 0.50

    def query(self, user_query: str, top_k: int = 4) -> Dict[str, Any]:
        """
        Semantically matches the user query against indexed FAQs & Tickets.
        Computes confidence score, categorizes intent, and decides escalation state.
        """
        if not user_query or not user_query.strip():
            return {
                "answer": "Please provide a query or select one of the suggested topics below.",
                "confidence": 0.0,
                "confidence_level": "LOW",
                "category": "General",
                "matched_source": None,
                "related_items": [],
                "escalate_needed": False,
                "suggested_ticket": None
            }

        cleaned_query = self._normalize_text(user_query)
        detected_category, cat_confidence = self.classify_category(user_query)

        if not self.vectorizer or self.tfidf_matrix is None:
            return self._fallback_response(user_query, detected_category)

        # Transform query vector
        query_vec = self.vectorizer.transform([cleaned_query])
        sims = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        # Apply keyword & category boosts
        boosted_sims = np.copy(sims)
        for idx, meta in enumerate(self.corpus_meta):
            title_norm = meta["title"].lower()
            query_words = [w for w in cleaned_query.split() if len(w) > 2]
            
            # Exact or partial word overlap with title & category
            matched_title_words = sum(1 for w in query_words if w in title_norm)
            if matched_title_words > 0:
                boosted_sims[idx] += min(0.35, matched_title_words * 0.12)

            # Category alignment bonus
            if meta["category"].lower() == detected_category.lower():
                boosted_sims[idx] += 0.10

            # Exact keyword match bonus from FAQ keywords or ticket tags
            if meta["type"] == "FAQ":
                kws = [k.lower() for k in meta["data"].get("keywords", [])]
                if any(kw in cleaned_query for kw in kws):
                    boosted_sims[idx] += 0.15
            elif meta["type"] == "TICKET":
                tags = [t.lower() for t in meta["data"].get("tags", [])]
                if any(t in cleaned_query for t in tags):
                    boosted_sims[idx] += 0.15

        # Scale and clip scores to [0.0, 0.98]
        boosted_sims = np.clip(boosted_sims, 0.0, 0.98)
        top_indices = np.argsort(boosted_sims)[::-1][:top_k]

        best_idx = top_indices[0]
        raw_score = float(boosted_sims[best_idx])
        confidence_score = round(raw_score, 3)

        # Confidence Levels:
        # HIGH: >= 0.55
        # MEDIUM: 0.35 <= score < 0.55
        # LOW: < 0.35
        if confidence_score >= 0.55:
            confidence_level = "HIGH"
        elif confidence_score >= 0.35:
            confidence_level = "MEDIUM"
        else:
            confidence_level = "LOW"

        top_meta = self.corpus_meta[best_idx]
        
        # Build related items list
        related_items = []
        for idx in top_indices[1:]:
            item_meta = self.corpus_meta[idx]
            item_score = float(boosted_sims[idx])
            if item_score > 0.15:
                related_items.append({
                    "id": item_meta["id"],
                    "title": item_meta["title"],
                    "type": item_meta["type"],
                    "category": item_meta["category"],
                    "confidence": round(item_score, 2)
                })

        # Format answer text based on match type
        if top_meta["type"] == "FAQ":
            faq_data = top_meta["data"]
            answer = faq_data.get("answer", "")
            suggested_actions = faq_data.get("suggested_actions", [])
            source_info = {
                "type": "FAQ",
                "id": faq_data.get("id"),
                "title": faq_data.get("question"),
                "category": faq_data.get("category"),
                "suggested_actions": suggested_actions
            }
        else:
            tck_data = top_meta["data"]
            answer = f"### Solution from Resolved Support Ticket: {tck_data.get('title')}\n\n"
            if tck_data.get("root_cause"):
                answer += f"**Root Cause:** {tck_data.get('root_cause')}\n\n"
            if tck_data.get("solution_steps"):
                answer += f"**Step-by-Step Fix:**\n{tck_data.get('solution_steps')}\n\n"
            if tck_data.get("verified_resolution"):
                answer += f"**Verified Resolution:** {tck_data.get('verified_resolution')}"
                
            source_info = {
                "type": "Historical Support Ticket",
                "id": tck_data.get("id") or tck_data.get("ticket_number"),
                "title": tck_data.get("title"),
                "category": tck_data.get("category"),
                "priority": tck_data.get("priority", "Medium"),
                "error_log": tck_data.get("error_log", "")
            }

        # Auto-Escalation Draft Generation for low or medium uncertainty
        escalate_needed = (confidence_level == "LOW")
        suggested_ticket = None
        if escalate_needed or confidence_level == "MEDIUM":
            suggested_ticket = {
                "title": self._generate_ticket_title(user_query, detected_category),
                "category": detected_category,
                "priority": "High" if any(w in user_query.lower() for w in ["deadline", "emergency", "broken", "critical", "fail", "rejected"]) else "Medium",
                "description": f"Intern Query: {user_query}\n\nAutomated Context: User reached out via AI Chat regarding '{detected_category}'. Bot matched with confidence {int(confidence_score*100)}%.",
                "suggested_tags": [detected_category.lower().replace(" ", "-"), "ai-chat-escalation"]
            }

        # Adjust answer if LOW confidence
        if confidence_level == "LOW":
            answer = (
                f"I couldn't find a direct verified solution in our internship knowledge base for: *\"{user_query}\"* (Confidence: {int(confidence_score*100)}%).\n\n"
                f"I've automatically prepared a **Support Escalation Ticket** for our coordinator and mentor team so you can get immediate 1-on-1 assistance."
            )

        return {
            "query": user_query,
            "answer": answer,
            "confidence": confidence_score,
            "confidence_percentage": int(confidence_score * 100),
            "confidence_level": confidence_level,
            "category": detected_category,
            "matched_source": source_info if confidence_level != "LOW" else None,
            "related_items": related_items[:3],
            "escalate_needed": escalate_needed,
            "suggested_ticket": suggested_ticket,
            "quick_chips": self.get_contextual_quick_chips(detected_category)
        }

    def _generate_ticket_title(self, query: str, category: str) -> str:
        """Extracts a succinct title for ticket escalation."""
        clean = query.strip()
        if len(clean) > 70:
            clean = clean[:67] + "..."
        # Capitalize first letter
        return f"[{category}] {clean[0].upper() + clean[1:]}"

    def get_contextual_quick_chips(self, category: str) -> List[str]:
        """Provides dynamic quick reply chips based on current topic context."""
        chips_map = {
            "Weekly Tasks & Submissions": [
                "What is the PR template?",
                "Is a Loom video required?",
                "When will task grades be released?"
            ],
            "GitHub & Version Control": [
                "Fix git push rejected error",
                "Branch naming rules",
                "How to sync upstream fork?",
                "Configure GitHub SSH key"
            ],
            "Deadlines & Extensions": [
                "What is the grace period?",
                "How to request 24h extension?",
                "Penalty for late submission"
            ],
            "Grading & Evaluations": [
                "What is the 4-pillar grading rubric?",
                "Can I resubmit a low score task?",
                "When are PR reviews completed?"
            ],
            "Certificates & Program Completion": [
                "What is the certificate passing grade?",
                "How to get Letter of Recommendation?",
                "Add certificate to LinkedIn"
            ],
            "Environment & Dependencies": [
                "Fix ModuleNotFoundError: fastapi",
                "Docker port 8000 already in use",
                "npm ERESOLVE dependency conflict"
            ]
        }
        return chips_map.get(category, [
            "How to submit weekly task?",
            "Git push rejected fix",
            "Deadline & grace period",
            "Certificate requirements",
            "Fix FastAPI CORS error"
        ])

    def _fallback_response(self, query: str, category: str) -> Dict[str, Any]:
        """Fallback when index is uninitialized."""
        return {
            "query": query,
            "answer": "System is initializing knowledge base index. Please try again in a few seconds.",
            "confidence": 0.30,
            "confidence_percentage": 30,
            "confidence_level": "LOW",
            "category": category,
            "matched_source": None,
            "related_items": [],
            "escalate_needed": True,
            "suggested_ticket": {
                "title": f"[{category}] Support Request: {query[:50]}",
                "category": category,
                "priority": "Medium",
                "description": query
            },
            "quick_chips": ["How to submit weekly task?", "Certificate criteria"]
        }
