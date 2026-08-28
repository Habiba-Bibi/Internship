#!/usr/bin/env python3
"""
Internship System Synthetic Data Generator
=========================================
Generates realistic sample data for an internship management and learning platform:
- 37 Tech Courses across 6 Career Fields
- 3 Prerequisite Rules (explicit course dependencies)
- 600 Intern Profiles
- 10,000 Course Ratings and Completion Records

Outputs standard CSV files into the 'data/' folder.
Zero external dependencies (uses standard Python library).
"""

import os
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================
RANDOM_SEED = 42
NUM_COURSES = 37
NUM_CAREER_FIELDS = 6
NUM_INTERNS = 600
NUM_RECORDS = 10000

OUTPUT_DIR = Path("data")

# Career Fields definition
CAREER_FIELDS = [
    "Web & Full-Stack Development",
    "Data Science & Artificial Intelligence",
    "Cloud Computing & DevOps",
    "Cybersecurity & Network Security",
    "Mobile App Development",
    "UI/UX & Product Design",
]

# Course catalogue (37 courses across 6 career fields: 7 + 6 + 6 + 6 + 6 + 6 = 37)
COURSES_DATA = [
    # 1. Web & Full-Stack Development (7 courses)
    {
        "course_id": "CRS-101",
        "course_title": "Frontend Fundamentals: HTML5, CSS3 & Responsive Design",
        "career_field": "Web & Full-Stack Development",
        "difficulty_level": "Beginner",
        "duration_weeks": 4,
        "credit_units": 3,
        "description": "Master the core building blocks of modern web pages, semantic HTML5, CSS flexbox, grid, and mobile-first layouts.",
    },
    {
        "course_id": "CRS-102",
        "course_title": "Modern JavaScript (ES6+) & TypeScript Core",
        "career_field": "Web & Full-Stack Development",
        "difficulty_level": "Beginner",
        "duration_weeks": 6,
        "credit_units": 3,
        "description": "Comprehensive grounding in asynchronous JS, DOM manipulation, promises, closures, and static typing with TypeScript.",
    },
    {
        "course_id": "CRS-103",
        "course_title": "Full-Stack Web Development with React & Next.js",
        "career_field": "Web & Full-Stack Development",
        "difficulty_level": "Intermediate",
        "duration_weeks": 8,
        "credit_units": 4,
        "description": "Build high-performance web applications with server-side rendering, component-driven design, and API routes.",
    },
    {
        "course_id": "CRS-104",
        "course_title": "Backend API Engineering with Node.js & Express",
        "career_field": "Web & Full-Stack Development",
        "difficulty_level": "Intermediate",
        "duration_weeks": 6,
        "credit_units": 3,
        "description": "Design secure, scalable RESTful microservices, authentication middleware, and robust API endpoints with Node.js.",
    },
    {
        "course_id": "CRS-105",
        "course_title": "Relational & NoSQL Database Systems (PostgreSQL & MongoDB)",
        "career_field": "Web & Full-Stack Development",
        "difficulty_level": "Intermediate",
        "duration_weeks": 5,
        "credit_units": 3,
        "description": "Database schema modeling, ACID transactions, complex indexing, query optimization, and document storage patterns.",
    },
    {
        "course_id": "CRS-106",
        "course_title": "Web Security, OAuth2 & Penetration Defense",
        "career_field": "Web & Full-Stack Development",
        "difficulty_level": "Advanced",
        "duration_weeks": 5,
        "credit_units": 3,
        "description": "Defend against OWASP Top 10 vulnerabilities, implement JWT/OAuth2 flows, CSRF protection, and zero-trust headers.",
    },
    {
        "course_id": "CRS-107",
        "course_title": "Distributed Systems & Event-Driven Microservices Architecture",
        "career_field": "Web & Full-Stack Development",
        "difficulty_level": "Advanced",
        "duration_weeks": 8,
        "credit_units": 4,
        "description": "Architect scalable event-driven systems using message brokers (Kafka/RabbitMQ), gRPC, and resilient caching patterns.",
    },

    # 2. Data Science & Artificial Intelligence (6 courses)
    {
        "course_id": "CRS-108",
        "course_title": "Python for Data Science & Scientific Computing",
        "career_field": "Data Science & Artificial Intelligence",
        "difficulty_level": "Beginner",
        "duration_weeks": 5,
        "credit_units": 3,
        "description": "Fundamental Python programming with NumPy, Pandas, vectorization, and data manipulation techniques.",
    },
    {
        "course_id": "CRS-109",
        "course_title": "Applied Statistics, Probability & Exploratory Data Analysis",
        "career_field": "Data Science & Artificial Intelligence",
        "difficulty_level": "Intermediate",
        "duration_weeks": 6,
        "credit_units": 3,
        "description": "Hypothesis testing, Bayesian reasoning, distribution fitting, feature engineering, and statistical storytelling.",
    },
    {
        "course_id": "CRS-110",
        "course_title": "Machine Learning Algorithms & Predictive Modeling",
        "career_field": "Data Science & Artificial Intelligence",
        "difficulty_level": "Intermediate",
        "duration_weeks": 8,
        "credit_units": 4,
        "description": "Supervised and unsupervised learning, regression, ensemble methods (XGBoost), cross-validation, and hyperparameter tuning.",
    },
    {
        "course_id": "CRS-111",
        "course_title": "Deep Learning Architectures with PyTorch & TensorFlow",
        "career_field": "Data Science & Artificial Intelligence",
        "difficulty_level": "Advanced",
        "duration_weeks": 8,
        "credit_units": 4,
        "description": "Train and optimize convolutional networks, recurrent models, attention mechanisms, and custom autograd models.",
    },
    {
        "course_id": "CRS-112",
        "course_title": "Natural Language Processing & Generative AI Systems",
        "career_field": "Data Science & Artificial Intelligence",
        "difficulty_level": "Advanced",
        "duration_weeks": 7,
        "credit_units": 4,
        "description": "Transformer architectures, tokenization, BERT/GPT fine-tuning, retrieval-augmented generation (RAG), and vector databases.",
    },
    {
        "course_id": "CRS-113",
        "course_title": "MLOps: Machine Learning Lifecycle & Production Deployment",
        "career_field": "Data Science & Artificial Intelligence",
        "difficulty_level": "Advanced",
        "duration_weeks": 6,
        "credit_units": 3,
        "description": "Model serving, experiment tracking with MLflow, data drift monitoring, automated retraining pipelines, and containerization.",
    },

    # 3. Cloud Computing & DevOps (6 courses)
    {
        "course_id": "CRS-114",
        "course_title": "Linux Systems Administration & Bash Automation",
        "career_field": "Cloud Computing & DevOps",
        "difficulty_level": "Beginner",
        "duration_weeks": 4,
        "credit_units": 2,
        "description": "Operating system fundamentals, file systems, permissions, process monitoring, cron scheduling, and automated shell scripts.",
    },
    {
        "course_id": "CRS-115",
        "course_title": "Cloud Infrastructure Fundamentals (AWS, Azure & GCP)",
        "career_field": "Cloud Computing & DevOps",
        "difficulty_level": "Beginner",
        "duration_weeks": 6,
        "credit_units": 3,
        "description": "Core cloud concepts: VPCs, compute instances, object storage, IAM policies, serverless functions, and cost management.",
    },
    {
        "course_id": "CRS-116",
        "course_title": "Containerization Essentials with Docker",
        "career_field": "Cloud Computing & DevOps",
        "difficulty_level": "Intermediate",
        "duration_weeks": 5,
        "credit_units": 3,
        "description": "Build multi-stage Docker images, manage container networking, storage volumes, and local multi-service orchestration with Compose.",
    },
    {
        "course_id": "CRS-117",
        "course_title": "CI/CD Pipelines & DevOps Automation",
        "career_field": "Cloud Computing & DevOps",
        "difficulty_level": "Intermediate",
        "duration_weeks": 6,
        "credit_units": 3,
        "description": "Automated build, test, and release pipelines using GitHub Actions, GitLab CI, artifact registries, and continuous delivery.",
    },
    {
        "course_id": "CRS-118",
        "course_title": "Kubernetes Cluster Management & Helm Packaging",
        "career_field": "Cloud Computing & DevOps",
        "difficulty_level": "Advanced",
        "duration_weeks": 8,
        "credit_units": 4,
        "description": "Production Kubernetes deployments, StatefulSets, Ingress controllers, Helm charts, autoscaling, and zero-downtime rollouts.",
    },
    {
        "course_id": "CRS-119",
        "course_title": "Infrastructure as Code (IaC) with Terraform & Ansible",
        "career_field": "Cloud Computing & DevOps",
        "difficulty_level": "Advanced",
        "duration_weeks": 6,
        "credit_units": 3,
        "description": "Declarative multi-cloud provisioning with Terraform modules, state locking, and configuration management via Ansible playbooks.",
    },

    # 4. Cybersecurity & Network Security (6 courses)
    {
        "course_id": "CRS-120",
        "course_title": "Computer Networking & Protocol Analysis (TCP/IP & Wireshark)",
        "career_field": "Cybersecurity & Network Security",
        "difficulty_level": "Beginner",
        "duration_weeks": 5,
        "credit_units": 3,
        "description": "OSI and TCP/IP stack analysis, subnetting, DNS/DHCP routing, packet inspection, and packet capture dissection with Wireshark.",
    },
    {
        "course_id": "CRS-121",
        "course_title": "Cybersecurity Fundamentals & Threat Modeling",
        "career_field": "Cybersecurity & Network Security",
        "difficulty_level": "Beginner",
        "duration_weeks": 5,
        "credit_units": 3,
        "description": "Security governance, STRIDE threat modeling, vulnerability classification, security controls, and compliance standards.",
    },
    {
        "course_id": "CRS-122",
        "course_title": "Ethical Hacking & Network Penetration Testing",
        "career_field": "Cybersecurity & Network Security",
        "difficulty_level": "Intermediate",
        "duration_weeks": 8,
        "credit_units": 4,
        "description": "Reconnaissance techniques, port scanning with Nmap, exploitation frameworks (Metasploit), privilege escalation, and reports.",
    },
    {
        "course_id": "CRS-123",
        "course_title": "Defensive Security, Next-Gen Firewalls & SIEM Systems",
        "career_field": "Cybersecurity & Network Security",
        "difficulty_level": "Intermediate",
        "duration_weeks": 6,
        "credit_units": 3,
        "description": "Security Operation Center (SOC) workflows, log aggregation with Splunk/Elastic, intrusion detection (Snort), and firewall tuning.",
    },
    {
        "course_id": "CRS-124",
        "course_title": "Applied Cryptography & Public Key Infrastructure (PKI)",
        "career_field": "Cybersecurity & Network Security",
        "difficulty_level": "Advanced",
        "duration_weeks": 6,
        "credit_units": 3,
        "description": "Symmetric and asymmetric encryption, TLS 1.3 handshakes, digital signatures, certificate authorities, and hashing algorithms.",
    },
    {
        "course_id": "CRS-125",
        "course_title": "Digital Forensics, Incident Response & Malware Analysis",
        "career_field": "Cybersecurity & Network Security",
        "difficulty_level": "Advanced",
        "duration_weeks": 7,
        "credit_units": 4,
        "description": "Evidence preservation, memory volatility analysis, disk imaging, triage forensics, and reverse-engineering suspicious binaries.",
    },

    # 5. Mobile App Development (6 courses)
    {
        "course_id": "CRS-126",
        "course_title": "Mobile UX Patterns & Human Interface Guidelines",
        "career_field": "Mobile App Development",
        "difficulty_level": "Beginner",
        "duration_weeks": 4,
        "credit_units": 2,
        "description": "Navigation patterns, touch targets, Material Design 3 guidelines, Apple HIG, responsive mobile form factors, and gestures.",
    },
    {
        "course_id": "CRS-127",
        "course_title": "Cross-Platform Mobile Apps with Flutter & Dart",
        "career_field": "Mobile App Development",
        "difficulty_level": "Intermediate",
        "duration_weeks": 8,
        "credit_units": 4,
        "description": "Build high-performance native iOS and Android apps with Flutter widgets, Bloc state management, and animations.",
    },
    {
        "course_id": "CRS-128",
        "course_title": "Cross-Platform Mobile Engineering with React Native",
        "career_field": "Mobile App Development",
        "difficulty_level": "Intermediate",
        "duration_weeks": 7,
        "credit_units": 4,
        "description": "Bridge web and native with React Native, Expo development workflow, native device APIs, and offline-first data sync.",
    },
    {
        "course_id": "CRS-129",
        "course_title": "Native Android App Development with Kotlin & Jetpack Compose",
        "career_field": "Mobile App Development",
        "difficulty_level": "Intermediate",
        "duration_weeks": 8,
        "credit_units": 4,
        "description": "Modern Android architecture with Jetpack Compose declarative UI, Coroutines/Flow, Room database, and MVVM design pattern.",
    },
    {
        "course_id": "CRS-130",
        "course_title": "Native iOS App Development with Swift & SwiftUI",
        "career_field": "Mobile App Development",
        "difficulty_level": "Intermediate",
        "duration_weeks": 8,
        "credit_units": 4,
        "description": "Construct iOS apps with SwiftUI, Combine reactive pipelines, CoreData/SwiftData, async/await concurrency, and widget extensions.",
    },
    {
        "course_id": "CRS-131",
        "course_title": "Mobile Application Security, Testing & App Store CI/CD",
        "career_field": "Mobile App Development",
        "difficulty_level": "Advanced",
        "duration_weeks": 5,
        "credit_units": 3,
        "description": "App sandboxing, reverse-engineering resistance, biometric auth, Fastlane deployment, and automated UI integration testing.",
    },

    # 6. UI/UX & Product Design (6 courses)
    {
        "course_id": "CRS-132",
        "course_title": "User Experience Research & Usability Testing Methods",
        "career_field": "UI/UX & Product Design",
        "difficulty_level": "Beginner",
        "duration_weeks": 4,
        "credit_units": 2,
        "description": "Qualitative and quantitative user interviews, persona creation, journey mapping, card sorting, and remote usability testing.",
    },
    {
        "course_id": "CRS-133",
        "course_title": "UI Design Systems & Interactive Prototyping with Figma",
        "career_field": "UI/UX & Product Design",
        "difficulty_level": "Beginner",
        "duration_weeks": 5,
        "credit_units": 3,
        "description": "Design tokens, auto-layout, component variants, responsive typography scales, and high-fidelity clickable Figma prototypes.",
    },
    {
        "course_id": "CRS-134",
        "course_title": "Interaction Design, Micro-Animations & Design Tokens",
        "career_field": "UI/UX & Product Design",
        "difficulty_level": "Intermediate",
        "duration_weeks": 5,
        "credit_units": 3,
        "description": "Motion physics, choreographing micro-interactions, state transitions, animated SVGs, and designer-developer handoff protocols.",
    },
    {
        "course_id": "CRS-135",
        "course_title": "Information Architecture & Wireframing Complex Systems",
        "career_field": "UI/UX & Product Design",
        "difficulty_level": "Intermediate",
        "duration_weeks": 4,
        "credit_units": 2,
        "description": "Site map hierarchies, navigation trees, content taxonomy, mental models, and rapid low-fidelity wireframing.",
    },
    {
        "course_id": "CRS-136",
        "course_title": "Digital Accessibility (WCAG 2.2) & Inclusive Design",
        "career_field": "UI/UX & Product Design",
        "difficulty_level": "Intermediate",
        "duration_weeks": 4,
        "credit_units": 2,
        "description": "Designing for color blindness, screen readers, keyboard navigation, accessible contrast ratios, and WCAG compliance audits.",
    },
    {
        "course_id": "CRS-137",
        "course_title": "Product Strategy, Design Systems at Scale & UX Metrics",
        "career_field": "UI/UX & Product Design",
        "difficulty_level": "Advanced",
        "duration_weeks": 6,
        "credit_units": 3,
        "description": "North Star metrics, HEART framework, scaling cross-functional enterprise design libraries, and calculating UX ROI.",
    },
]

# The 3 explicit prerequisite rules (which course to take first)
PREREQUISITE_RULES = [
    {
        "rule_id": "PREREQ-1",
        "target_course_id": "CRS-110",
        "target_course_title": "Machine Learning Algorithms & Predictive Modeling",
        "prerequisite_course_id": "CRS-108",
        "prerequisite_course_title": "Python for Data Science & Scientific Computing",
        "rule_description": "Must complete Python for Data Science (CRS-108) before attempting Machine Learning Algorithms (CRS-110).",
        "enforcement_level": "Strict",
    },
    {
        "rule_id": "PREREQ-2",
        "target_course_id": "CRS-103",
        "target_course_title": "Full-Stack Web Development with React & Next.js",
        "prerequisite_course_id": "CRS-102",
        "prerequisite_course_title": "Modern JavaScript (ES6+) & TypeScript Core",
        "rule_description": "Must complete Modern JavaScript & TypeScript (CRS-102) before enrolling in Full-Stack Web Development (CRS-103).",
        "enforcement_level": "Strict",
    },
    {
        "rule_id": "PREREQ-3",
        "target_course_id": "CRS-117",
        "target_course_title": "CI/CD Pipelines & DevOps Automation",
        "prerequisite_course_id": "CRS-115",
        "prerequisite_course_title": "Cloud Infrastructure Fundamentals (AWS, Azure & GCP)",
        "rule_description": "Must complete Cloud Infrastructure Fundamentals (CRS-115) before taking CI/CD Pipelines & DevOps Automation (CRS-117).",
        "enforcement_level": "Strict",
    },
]

# Name pools for realistic intern profile generation
FIRST_NAMES = [
    "Aarav", "Aditi", "Ahmed", "Alex", "Ali", "Amara", "Ananya", "Andreas",
    "Beatriz", "Benjamin", "Bilal", "Brenda", "Carlos", "Chloe", "Daniel", "David",
    "Elena", "Emily", "Ethan", "Fatima", "Gabriel", "Grace", "Hassan", "Hannah",
    "Ibrahim", "Isabella", "Jack", "Jasmine", "Javier", "Jordan", "Kai", "Kavya",
    "Liam", "Lucas", "Maya", "Mei", "Mohammed", "Nadia", "Noah", "Olivia",
    "Omar", "Priya", "Rahul", "Rania", "Samira", "Samuel", "Sarah", "Sophia",
    "Tariq", "Thomas", "Valentina", "Victor", "Wei", "William", "Yara", "Yuki",
    "Zainab", "Zara", "Zayd", "Zoey"
]

LAST_NAMES = [
    "Al-Mansoor", "Anderson", "Chen", "Chowdhury", "Costa", "Das", "Diallo",
    "Dubois", "Fernandez", "Garcia", "Gomez", "Gupta", "Hansen", "Hassan",
    "Hernandez", "Ibrahim", "Ivanov", "Jackson", "Johnson", "Kaur", "Khan",
    "Kim", "Kowalski", "Kumar", "Lee", "Lopez", "Mahmoud", "Martin",
    "Mendoza", "Miller", "Morales", "Muller", "Nakamura", "Novak", "O'Connor",
    "Patel", "Pereira", "Popov", "Rahman", "Reyes", "Rodriguez", "Rossi",
    "Santos", "Sato", "Schmidt", "Sharma", "Silva", "Smith", "Suzuki",
    "Tanaka", "Taylor", "Torres", "Tran", "Vargas", "Wang", "Williams",
    "Wilson", "Wu", "Yamamoto", "Zhang"
]

EDUCATION_LEVELS = [
    ("Undergraduate Student", 0.50),
    ("Master's Degree Student", 0.25),
    ("Bootcamp Graduate", 0.15),
    ("Career Switcher", 0.10),
]

MAJORS = [
    "Computer Science",
    "Software Engineering",
    "Data Science & Analytics",
    "Information Technology",
    "Computer Engineering",
    "Electrical Engineering",
    "Mathematics & Statistics",
    "Graphic & Interaction Design",
    "Business Information Systems",
]

INTERN_STATUSES = [
    ("Active", 0.70),
    ("Graduated", 0.20),
    ("Placed in Tech Role", 0.08),
    ("On Leave", 0.02),
]

REVIEW_COMMENTS_BY_RATING = {
    5: [
        "Exceptional course! Hands-on labs were directly applicable to real-world projects.",
        "Clear explanations, great mentorship, and practical coding exercises. Highly recommend!",
        "The project assignments were challenging but extremely rewarding.",
        "One of the best technical modules in this internship track.",
        "Fantastic coverage of modern industry best practices. 10/10!",
        "Loved the real-world scenarios and comprehensive code reviews.",
        "Exceeded my expectations. I feel confident applying these skills in interviews.",
    ],
    4: [
        "Very thorough and well-structured curriculum. Enjoyed the coding challenges.",
        "Solid content and great practical labs, though some topics could use more deep-dives.",
        "Good balance between theoretical concepts and practical applications.",
        "Insightful lectures and helpful support from teaching assistants.",
        "A great learning curve. The final project helped tie all concepts together.",
        "Learned a huge amount in a short timeframe. Would take again.",
    ],
    3: [
        "Decent course overall, but some of the assignment instructions were slightly ambiguous.",
        "Good introductory material, but felt a bit rushed towards the final weeks.",
        "Fair overview of the topic. More real-time troubleshooting examples would be nice.",
        "Content is good, but requires quite a bit of independent research to finish assignments.",
    ],
    2: [
        "Found the pace uneven. The initial modules were basic, but the final project was abruptly difficult.",
        "Lab environments had occasional setup issues that slowed down progress.",
        "Could use more modern examples and clearer explanations on complex topics.",
    ],
    1: [
        "Material felt outdated and the grading feedback was too brief to be helpful.",
        "Struggled with lack of detailed documentation in the lab environments.",
        "Did not match my learning style; prerequisites were harder than indicated.",
    ]
}


def weighted_choice(choices):
    """Helper to pick an option based on weighted probabilities."""
    items, weights = zip(*choices)
    return random.choices(items, weights=weights, k=1)[0]


def random_date(start_date: datetime, end_date: datetime) -> datetime:
    """Generate a random datetime between start_date and end_date."""
    delta_seconds = int((end_date - start_date).total_seconds())
    random_second = random.randint(0, delta_seconds)
    return start_date + timedelta(seconds=random_second)


# ==============================================================================
# DATA GENERATION FUNCTIONS
# ==============================================================================

def generate_courses():
    """Returns the 37 course dictionaries."""
    assert len(COURSES_DATA) == NUM_COURSES, f"Expected {NUM_COURSES} courses, got {len(COURSES_DATA)}"
    return COURSES_DATA


def generate_prerequisite_rules():
    """Returns the 3 prerequisite rules."""
    assert len(PREREQUISITE_RULES) == 3, f"Expected 3 prerequisite rules, got {len(PREREQUISITE_RULES)}"
    return PREREQUISITE_RULES


def generate_interns():
    """Generate 600 realistic intern profiles."""
    interns = []
    start_date_range = datetime(2024, 9, 1)
    end_date_range = datetime(2026, 6, 1)
    used_emails = set()

    for i in range(1, NUM_INTERNS + 1):
        intern_id = f"INT-{i:04d}"
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        
        # Gender representation
        gender = random.choice(["Female", "Male", "Non-Binary"])

        # Realistic unique email
        clean_first = first_name.lower()
        clean_last = last_name.lower().replace("'", "").replace("-", "")
        email_candidate = f"{clean_first}.{clean_last}{i}@internship.org"
        used_emails.add(email_candidate)

        education = weighted_choice(EDUCATION_LEVELS)
        major = random.choice(MAJORS)
        primary_track = random.choice(CAREER_FIELDS)
        status = weighted_choice(INTERN_STATUSES)
        
        join_dt = random_date(start_date_range, end_date_range)
        join_date_str = join_dt.strftime("%Y-%m-%d")

        interns.append({
            "intern_id": intern_id,
            "first_name": first_name,
            "last_name": last_name,
            "gender": gender,
            "email": email_candidate,
            "education_level": education,
            "academic_major": major,
            "primary_career_field": primary_track,
            "join_date": join_date_str,
            "status": status,
        })

    return interns


def generate_ratings_and_completions(interns, courses, prereq_rules):
    """
    Generate exactly 10,000 course rating and completion records.
    Enforces the 3 prerequisite rules chronologically:
    - Rule 1: CRS-108 must be completed before CRS-110.
    - Rule 2: CRS-102 must be completed before CRS-103.
    - Rule 3: CRS-115 must be completed before CRS-117.
    Guarantees 100% prerequisite rule compliance with zero violations.
    """
    course_map = {c["course_id"]: c for c in courses}
    intern_map = {intern["intern_id"]: intern for intern in interns}

    # Map target courses to their prerequisite requirement: target_id -> prereq_id
    prereq_map = {rule["target_course_id"]: rule["prerequisite_course_id"] for rule in prereq_rules}

    # Pre-build candidate courses by career field
    courses_by_field = {}
    for c in courses:
        field = c["career_field"]
        courses_by_field.setdefault(field, []).append(c["course_id"])
    all_course_ids = [c["course_id"] for c in courses]

    system_cutoff_date = datetime(2026, 8, 20)
    rating_weights = [(5, 0.45), (4, 0.35), (3, 0.12), (2, 0.05), (1, 0.03)]

    # Allocate total records across all 600 interns so sum is exactly 10,000
    # Average ~16.67 courses per intern (range 12 to 22)
    counts = [16] * NUM_INTERNS
    remainder = NUM_RECORDS - sum(counts)  # 10000 - 9600 = 400
    # Distribute remainder
    for idx in range(remainder):
        counts[idx] += 1
    random.shuffle(counts)
    assert sum(counts) == NUM_RECORDS

    all_records = []
    record_id_counter = 1

    for intern, num_courses_for_intern in zip(interns, counts):
        intern_id = intern["intern_id"]
        join_dt = datetime.strptime(intern["join_date"], "%Y-%m-%d")
        primary_track = intern["primary_career_field"]
        track_courses = courses_by_field.get(primary_track, [])

        # Track courses taken by this intern: course_id -> record dict
        intern_taken = {}
        # Timeline pointer for this intern
        current_time = join_dt + timedelta(days=random.randint(1, 10))

        for _ in range(num_courses_for_intern):
            # Determine eligible courses:
            # 1. Not already taken by this intern
            # 2. If it has a prerequisite, prerequisite MUST be already completed
            eligible_courses = []
            for cid in all_course_ids:
                if cid in intern_taken:
                    continue
                if cid in prereq_map:
                    prereq_id = prereq_map[cid]
                    # Check if prereq was taken and completed
                    if prereq_id not in intern_taken:
                        continue
                    if intern_taken[prereq_id]["completion_status"] != "Completed":
                        continue
                eligible_courses.append(cid)

            if not eligible_courses:
                break

            # Weighted choice towards primary track
            primary_eligible = [cid for cid in eligible_courses if cid in track_courses]
            if primary_eligible and random.random() < 0.60:
                chosen_course_id = random.choice(primary_eligible)
            else:
                # If a foundational prerequisite is available, give it a slight boost
                foundational_prereqs = [cid for cid in eligible_courses if cid in prereq_map.values()]
                if foundational_prereqs and random.random() < 0.30:
                    chosen_course_id = random.choice(foundational_prereqs)
                else:
                    chosen_course_id = random.choice(eligible_courses)

            course_obj = course_map[chosen_course_id]
            duration_weeks = course_obj["duration_weeks"]
            duration_days = duration_weeks * 7

            # Calculate enrollment date
            # Must be after intern join date
            enrollment_dt = current_time
            # If chosen course has a prerequisite, ensure enrollment_dt > prerequisite completion date
            if chosen_course_id in prereq_map:
                prereq_id = prereq_map[chosen_course_id]
                prereq_comp_dt = intern_taken[prereq_id]["completion_dt"]
                if prereq_comp_dt and enrollment_dt <= prereq_comp_dt:
                    enrollment_dt = prereq_comp_dt + timedelta(days=random.randint(1, 10))

            # Ensure enrollment doesn't exceed cutoff
            if enrollment_dt >= system_cutoff_date - timedelta(days=7):
                enrollment_dt = system_cutoff_date - timedelta(days=random.randint(8, 30))
                # Double check prereq constraint after adjusting
                if chosen_course_id in prereq_map:
                    prereq_comp_dt = intern_taken[prereq_map[chosen_course_id]]["completion_dt"]
                    if prereq_comp_dt and enrollment_dt <= prereq_comp_dt:
                        enrollment_dt = prereq_comp_dt + timedelta(days=1)

            # Determine status based on time remaining before system cutoff
            days_until_cutoff = (system_cutoff_date - enrollment_dt).days
            if days_until_cutoff < duration_days // 2:
                # Too recent, definitely In Progress
                status = "In Progress"
            else:
                roll = random.random()
                if roll < 0.80:
                    status = "Completed"
                elif roll < 0.92:
                    status = "In Progress"
                else:
                    status = "Dropped"

            # Compute fields based on status
            if status == "Completed":
                actual_duration = random.randint(max(7, duration_days - 4), duration_days + 14)
                comp_dt = enrollment_dt + timedelta(days=actual_duration)
                if comp_dt > system_cutoff_date:
                    comp_dt = system_cutoff_date - timedelta(days=random.randint(1, 3))
                comp_date_str = comp_dt.strftime("%Y-%m-%d")
                progress_pct = 100
                score = round(random.uniform(70.0, 99.5), 1)
                rating = weighted_choice(rating_weights)
                comment = random.choice(REVIEW_COMMENTS_BY_RATING[rating])
            elif status == "In Progress":
                comp_dt = None
                comp_date_str = ""
                progress_pct = random.randint(15, 85)
                score = ""
                if random.random() < 0.35:
                    rating = weighted_choice([(5, 0.40), (4, 0.45), (3, 0.15)])
                    comment = random.choice(REVIEW_COMMENTS_BY_RATING[rating])
                else:
                    rating = ""
                    comment = "Course currently in progress."
            else:  # Dropped
                comp_dt = None
                comp_date_str = ""
                progress_pct = random.randint(5, 45)
                score = round(random.uniform(20.0, 58.0), 1) if random.random() < 0.5 else ""
                if random.random() < 0.55:
                    rating = weighted_choice([(3, 0.30), (2, 0.45), (1, 0.25)])
                    comment = random.choice(REVIEW_COMMENTS_BY_RATING[rating])
                else:
                    rating = ""
                    comment = "Withdrew from module due to scheduling conflicts."

            # Advance current_time for next course:
            # Allows some concurrent overlap or sequential spacing
            if comp_dt:
                if random.random() < 0.65:
                    current_time = comp_dt + timedelta(days=random.randint(2, 14))
                else:
                    current_time = enrollment_dt + timedelta(days=random.randint(7, 21))
            else:
                current_time = enrollment_dt + timedelta(days=random.randint(14, 30))

            if current_time > system_cutoff_date - timedelta(days=14):
                current_time = join_dt + timedelta(days=random.randint(30, 90))

            record = {
                "record_id": f"REC-{record_id_counter:06d}",
                "intern_id": intern_id,
                "course_id": chosen_course_id,
                "enrollment_date": enrollment_dt.strftime("%Y-%m-%d"),
                "completion_status": status,
                "completion_date": comp_date_str,
                "progress_percent": progress_pct,
                "score": score,
                "rating": rating,
                "review_comment": comment,
                "prerequisite_satisfied": True,
                # internal metadata
                "_completion_dt": comp_dt,
            }
            record_id_counter += 1

            intern_taken[chosen_course_id] = {
                "completion_status": status,
                "enrollment_dt": enrollment_dt,
                "completion_dt": comp_dt,
            }
            all_records.append(record)

    # If any intern had fewer courses due to edge case, top up to exactly NUM_RECORDS
    while len(all_records) < NUM_RECORDS:
        # Pick an intern and an eligible course
        intern = random.choice(interns)
        intern_id = intern["intern_id"]
        join_dt = datetime.strptime(intern["join_date"], "%Y-%m-%d")
        existing_courses = {r["course_id"] for r in all_records if r["intern_id"] == intern_id}
        avail = [c for c in all_course_ids if c not in existing_courses and c not in prereq_map]
        if not avail:
            continue
        c_id = random.choice(avail)
        enr_dt = join_dt + timedelta(days=random.randint(5, 60))
        dur_days = course_map[c_id]["duration_weeks"] * 7
        comp_dt = enr_dt + timedelta(days=dur_days + random.randint(1, 7))
        rt = weighted_choice(rating_weights)
        all_records.append({
            "record_id": f"REC-{record_id_counter:06d}",
            "intern_id": intern_id,
            "course_id": c_id,
            "enrollment_date": enr_dt.strftime("%Y-%m-%d"),
            "completion_status": "Completed",
            "completion_date": comp_dt.strftime("%Y-%m-%d"),
            "progress_percent": 100,
            "score": round(random.uniform(75.0, 98.0), 1),
            "rating": rt,
            "review_comment": random.choice(REVIEW_COMMENTS_BY_RATING[rt]),
            "prerequisite_satisfied": True,
            "_completion_dt": comp_dt,
        })
        record_id_counter += 1

    # Remove internal metadata key before saving
    for r in all_records:
        r.pop("_completion_dt", None)

    return all_records

    return records


# ==============================================================================
# CSV EXPORT UTILITIES
# ==============================================================================

def write_csv(filepath: Path, fieldnames: list, rows: list):
    """Writes a list of dictionaries to a CSV file with utf-8 encoding."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  -> Saved {len(rows):,} rows to {filepath}")


# ==============================================================================
# MAIN PIPELINE & VALIDATION
# ==============================================================================

def main():
    print("=" * 70)
    print("INTERNSHIP SYSTEM - SYNTHETIC DATA GENERATION PIPELINE")
    print("=" * 70)

    # Set seed for reproducible results
    random.seed(RANDOM_SEED)

    # 1. Generate Courses
    print("\n[1/4] Generating Courses...")
    courses = generate_courses()
    courses_file = OUTPUT_DIR / "courses.csv"
    write_csv(courses_file, list(courses[0].keys()), courses)

    # 2. Generate Prerequisite Rules
    print("\n[2/4] Generating Prerequisite Rules...")
    prereq_rules = generate_prerequisite_rules()
    prereq_file = OUTPUT_DIR / "prerequisite_rules.csv"
    write_csv(prereq_file, list(prereq_rules[0].keys()), prereq_rules)

    # 3. Generate Intern Profiles
    print("\n[3/4] Generating Intern Profiles...")
    interns = generate_interns()
    interns_file = OUTPUT_DIR / "interns.csv"
    write_csv(interns_file, list(interns[0].keys()), interns)

    # 4. Generate Course Ratings & Completion Records
    print("\n[4/4] Generating Ratings & Completion Records...")
    records = generate_ratings_and_completions(interns, courses, prereq_rules)
    records_file = OUTPUT_DIR / "ratings_and_completions.csv"
    write_csv(records_file, list(records[0].keys()), records)

    # ==========================================================================
    # DATASET VALIDATION REPORT
    # ==========================================================================
    print("\n" + "=" * 70)
    print("DATA INTEGRITY VERIFICATION REPORT")
    print("=" * 70)

    # Verification 1: Courses count & Career fields
    unique_fields = {c["career_field"] for c in courses}
    print(f"Total Courses: {len(courses)} (Expected: {NUM_COURSES})")
    print(f"Unique Career Fields: {len(unique_fields)} (Expected: {NUM_CAREER_FIELDS})")
    for field in CAREER_FIELDS:
        count = sum(1 for c in courses if c["career_field"] == field)
        print(f"  - {field}: {count} courses")

    # Verification 2: Prerequisite rules count
    print(f"\nTotal Prerequisite Rules: {len(prereq_rules)} (Expected: 3)")
    for rule in prereq_rules:
        print(f"  - {rule['rule_id']}: {rule['prerequisite_course_id']} -> {rule['target_course_id']} ({rule['target_course_title']})")

    # Verification 3: Interns count
    print(f"\nTotal Interns: {len(interns)} (Expected: {NUM_INTERNS})")
    gender_counts = {}
    for intern in interns:
        gender_counts[intern["gender"]] = gender_counts.get(intern["gender"], 0) + 1
    print(f"  - Gender distribution: {gender_counts}")

    # Verification 4: Ratings and completion records
    print(f"\nTotal Rating/Completion Records: {len(records)} (Expected: {NUM_RECORDS})")
    status_counts = {}
    rating_counts = {}
    prereq_satisfied_count = 0
    for r in records:
        st = r["completion_status"]
        status_counts[st] = status_counts.get(st, 0) + 1
        rt = r["rating"]
        if rt != "":
            rating_counts[rt] = rating_counts.get(rt, 0) + 1
        if r["prerequisite_satisfied"]:
            prereq_satisfied_count += 1

    print(f"  - Completion Status breakdown: {status_counts}")
    print(f"  - Star Ratings breakdown: {sorted(rating_counts.items())}")
    print(f"  - Prerequisite Satisfied: {prereq_satisfied_count} / {len(records)} ({prereq_satisfied_count / len(records) * 100:.2f}%)")

    # Verification 5: Verify strict prerequisite compliance
    # Check that for any completed target course, the prerequisite was completed prior
    prereq_violations = 0
    history_by_intern = {intern["intern_id"]: {} for intern in interns}
    for r in records:
        history_by_intern[r["intern_id"]][r["course_id"]] = r

    prereq_map = {rule["target_course_id"]: rule["prerequisite_course_id"] for rule in prereq_rules}
    for intern_id, hist in history_by_intern.items():
        for target_id, prereq_id in prereq_map.items():
            if target_id in hist and hist[target_id]["completion_status"] == "Completed":
                target_enroll_dt = hist[target_id]["enrollment_date"]
                if prereq_id not in hist:
                    prereq_violations += 1
                elif hist[prereq_id]["completion_status"] != "Completed":
                    prereq_violations += 1
                elif hist[prereq_id]["completion_date"] > target_enroll_dt:
                    prereq_violations += 1

    print(f"  - Strict Prerequisite Rule Violations: {prereq_violations} (Must be 0)")
    assert prereq_violations == 0, f"Found {prereq_violations} prerequisite violations!"
    print("\nALL INTEGRITY CONSTRAINTS VERIFIED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    main()
