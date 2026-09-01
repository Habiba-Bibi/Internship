"""
generate_data.py
Generates realistic datasets for Intern Skills and Industry Job Postings,
along with a Skills Taxonomy and Curated Course Catalog.
"""

import os
import json
import random
import pandas as pd
from typing import List, Dict, Any

# Set random seed for reproducibility
random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
os.makedirs(DATA_DIR, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. SKILLS TAXONOMY
# -----------------------------------------------------------------------------
DOMAINS = {
    "AI & Machine Learning": {
        "roles": [
            "Machine Learning Engineer", "Data Scientist", "AI Research Intern",
            "NLP Engineer", "Computer Vision Engineer", "Deep Learning Specialist"
        ],
        "core_skills": ["Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "scikit-learn", "Data Analysis", "Pandas", "NumPy", "Statistics", "Mathematics"],
        "advanced_skills": ["Transformers", "Large Language Models", "Hugging Face", "MLOps", "Computer Vision", "NLP", "Model Deployment", "LangChain", "Vector Databases"],
        "tools": ["Jupyter", "Docker", "Git", "Weights & Biases", "FastAPI", "MLflow", "CUDA", "AWS SageMaker"]
    },
    "Full Stack Web Development": {
        "roles": [
            "Full Stack Developer", "Frontend Engineer", "Backend Developer",
            "React / Node.js Developer", "Software Engineer - Web", "Web Application Intern"
        ],
        "core_skills": ["JavaScript", "TypeScript", "HTML5", "CSS3", "React", "Node.js", "Express.js", "REST APIs", "SQL", "Git"],
        "advanced_skills": ["Next.js", "GraphQL", "Redux", "Tailwind CSS", "Microservices", "WebSockets", "Authentication & JWT", "PostgreSQL", "MongoDB"],
        "tools": ["VS Code", "Postman", "Docker", "Webpack", "Vite", "Jest", "GitHub Actions", "Vercel", "Redis"]
    },
    "Cloud Architecture & DevOps": {
        "roles": [
            "DevOps Engineer", "Cloud Infrastructure Engineer", "Site Reliability Engineer (SRE)",
            "Cloud Security Engineer", "Platform Engineer", "DevOps Intern"
        ],
        "core_skills": ["Linux", "Bash Scripting", "Docker", "Kubernetes", "CI/CD", "Git", "Networking Basics", "Cloud Computing"],
        "advanced_skills": ["Terraform", "Infrastructure as Code", "AWS", "Azure", "GCP", "Ansible", "Helm", "Prometheus", "Grafana", "Service Mesh"],
        "tools": ["GitLab CI", "Jenkins", "ArgoCD", "Vault", "Terraform Cloud", "ELK Stack", "Datadog", "Nginx"]
    },
    "Cybersecurity & Network Defense": {
        "roles": [
            "Cybersecurity Analyst", "Security Engineer", "SOC Analyst",
            "Penetration Tester", "Information Security Intern", "Threat Intelligence Analyst"
        ],
        "core_skills": ["Network Security", "Linux", "Python", "Cryptography", "Vulnerability Assessment", "Firewalls", "TCP/IP", "Security Fundamentals"],
        "advanced_skills": ["Penetration Testing", "SIEM", "Incident Response", "OWASP Top 10", "Ethical Hacking", "Forensics", "Cloud Security", "Identity & Access Management (IAM)"],
        "tools": ["Wireshark", "Burp Suite", "Metasploit", "Splunk", "Nmap", "Kali Linux", "Snort", "Nessus"]
    },
    "Mobile Application Development": {
        "roles": [
            "Mobile App Developer", "Flutter Developer", "iOS Engineer",
            "Android Developer", "React Native Developer", "Mobile Software Intern"
        ],
        "core_skills": ["Dart", "Flutter", "Kotlin", "Swift", "React Native", "Mobile UI Design", "REST APIs", "Git", "State Management"],
        "advanced_skills": ["SwiftUI", "Jetpack Compose", "CoreData", "Room Database", "Push Notifications", "App Store Deployment", "Offline Sync", "Performance Optimization"],
        "tools": ["Android Studio", "Xcode", "Firebase", "Postman", "Fastlane", "Figma", "CocoaPods", "Gradle"]
    },
    "Data Engineering & Big Data": {
        "roles": [
            "Data Engineer", "Big Data Developer", "ETL Developer",
            "Data Platform Engineer", "Analytics Engineer", "Data Pipeline Intern"
        ],
        "core_skills": ["Python", "SQL", "Data Pipelines", "ETL", "Relational Databases", "Data Warehousing", "Git", "Linux"],
        "advanced_skills": ["Apache Spark", "Apache Kafka", "Airflow", "Snowflake", "dbt", "Hadoop", "PySpark", "Data Modeling", "BigQuery"],
        "tools": ["Docker", "AWS S3", "Databricks", "Redshift", "PostgreSQL", "Kafka Connect", "Tableau", "MinIO"]
    },
    "Business Intelligence & Analytics": {
        "roles": [
            "Business Intelligence Analyst", "Data Analyst", "Product Analyst",
            "BI Developer", "Marketing Analytics Intern", "Operations Analyst"
        ],
        "core_skills": ["SQL", "Data Visualization", "Excel & Spreadsheets", "Tableau", "Power BI", "Exploratory Data Analysis", "Business Metrics", "Statistics"],
        "advanced_skills": ["Python for Analytics", "A/B Testing", "Cohort Analysis", "Data Storytelling", "DAX", "Predictive Analytics", "Google Analytics 4", "ETL Basics"],
        "tools": ["Tableau Desktop", "Power BI Service", "Jupyter", "Looker", "SQL Server", "Metabase", "Mixpanel", "HubSpot"]
    },
    "Embedded Systems & IoT": {
        "roles": [
            "Embedded Software Engineer", "IoT Systems Engineer", "Firmware Developer",
            "Hardware/Software Integrator", "Robotics Software Intern", "Embedded Linux Developer"
        ],
        "core_skills": ["C", "C++", "Microcontrollers", "RTOS", "Embedded C", "UART/SPI/I2C Protocols", "Linux", "Electronics Fundamentals"],
        "advanced_skills": ["FreeRTOS", "Embedded Linux", "BLE / Zigbee", "MQTT", "Device Drivers", "Hardware Debugging", "ARM Architecture", "PCB Basics"],
        "tools": ["PlatformIO", "Keil uVision", "STM32CubeIDE", "Oscilloscope", "Logic Analyzer", "Raspberry Pi", "Arduino", "ESP32"]
    }
}

SOFT_SKILLS = [
    "Problem Solving", "Critical Thinking", "Agile & Scrum", "Communication",
    "Team Collaboration", "Time Management", "Code Documentation", "Technical Writing",
    "Adaptability", "Presentation Skills"
]

# -----------------------------------------------------------------------------
# 2. COURSE CATALOG & TRAINING ROADMAPS
# -----------------------------------------------------------------------------
def build_course_catalog() -> Dict[str, Dict[str, Any]]:
    catalog = {
        # AI & ML
        "Python": {
            "title": "Python for Data Science & Software Engineering",
            "platform": "Coursera (IBM / DeepLearning.AI)",
            "duration_weeks": 4,
            "level": "Beginner",
            "project": "Build an Automated Data Extraction & ETL Script with Unit Tests",
            "certification": "PCEP - Certified Entry-Level Python Programmer"
        },
        "Machine Learning": {
            "title": "Machine Learning Specialization",
            "platform": "Coursera (Stanford Online & DeepLearning.AI)",
            "duration_weeks": 8,
            "level": "Intermediate",
            "project": "End-to-End Customer Churn Prediction & Scoring API",
            "certification": "DeepLearning.AI Machine Learning Certificate"
        },
        "Deep Learning": {
            "title": "Deep Learning Specialization (Neural Networks, CNN, RNN)",
            "platform": "Coursera (DeepLearning.AI)",
            "duration_weeks": 8,
            "level": "Advanced",
            "project": "Medical Image Classification & Segmentation Model",
            "certification": "DeepLearning.AI Deep Learning Specialization"
        },
        "TensorFlow": {
            "title": "TensorFlow Developer Certificate Program",
            "platform": "Coursera (DeepLearning.AI)",
            "duration_weeks": 6,
            "level": "Intermediate",
            "project": "Real-time Object Detection with TensorFlow & OpenCV",
            "certification": "Google TensorFlow Certified Developer"
        },
        "PyTorch": {
            "title": "Deep Learning with PyTorch: Zero to GANs",
            "platform": "edX / Jovian",
            "duration_weeks": 6,
            "level": "Intermediate",
            "project": "Custom Transformer Model for Sentiment & Intent Analysis",
            "certification": "PyTorch for Deep Learning Specialist"
        },
        "MLOps": {
            "title": "Machine Learning Engineering for Production (MLOps)",
            "platform": "Coursera (DeepLearning.AI)",
            "duration_weeks": 6,
            "level": "Advanced",
            "project": "Continuous ML Training & Deployment Pipeline with MLflow & Docker",
            "certification": "Databricks Certified MLOps Practitioner"
        },
        "Large Language Models": {
            "title": "Generative AI with Large Language Models",
            "platform": "Coursera (AWS & DeepLearning.AI)",
            "duration_weeks": 4,
            "level": "Advanced",
            "project": "RAG (Retrieval-Augmented Generation) Assistant with LangChain & FAISS",
            "certification": "Generative AI Specialist Certification"
        },
        "LangChain": {
            "title": "LangChain for LLM Application Development",
            "platform": "DeepLearning.AI Short Courses",
            "duration_weeks": 3,
            "level": "Advanced",
            "project": "Autonomous Research Agent with Tool Calling & Memory",
            "certification": "LangChain Certified Associate"
        },

        # Web & Full Stack
        "React": {
            "title": "Modern React with Redux & Hooks",
            "platform": "Udemy (Stephen Grider) / freeCodeCamp",
            "duration_weeks": 5,
            "level": "Intermediate",
            "project": "Full-Featured Collaborative Kanban Workspace with Real-time Sync",
            "certification": "Meta Front-End Developer Professional Certificate"
        },
        "Node.js": {
            "title": "Complete NodeJS Developer: REST, GraphQL, Microservices",
            "platform": "Udemy (Zero To Mastery)",
            "duration_weeks": 6,
            "level": "Intermediate",
            "project": "Scalable E-Commerce Backend API with Stripe & Rate Limiting",
            "certification": "OpenJS Node.js Application Developer (JSNAD)"
        },
        "TypeScript": {
            "title": "Understanding TypeScript: Modern TS from Scratch",
            "platform": "Udemy (Maximilian Schwarzmüller)",
            "duration_weeks": 4,
            "level": "Intermediate",
            "project": "Type-Safe Full-Stack SaaS Dashboard with Prisma & Next.js",
            "certification": "TypeScript Professional Specialist"
        },
        "Next.js": {
            "title": "Next.js 14 App Router: The Complete Guide",
            "platform": "Udemy / Vercel Learn",
            "duration_weeks": 4,
            "level": "Intermediate",
            "project": "Server-Side Rendered Multi-Tenant Blog & Knowledge Base",
            "certification": "Vercel Next.js Developer Badge"
        },
        "GraphQL": {
            "title": "GraphQL with Node, React & Apollo Client",
            "platform": "Frontend Masters",
            "duration_weeks": 3,
            "level": "Intermediate",
            "project": "Social Media Feed API with Subscriptions & Caching",
            "certification": "Apollo GraphQL Associate"
        },
        "REST APIs": {
            "title": "RESTful API Design, Security and Best Practices",
            "platform": "Pluralsight",
            "duration_weeks": 3,
            "level": "Beginner",
            "project": "Secure Banking API with JWT, OAuth2, and Swagger Documentation",
            "certification": "Postman API Fundamentals Student Expert"
        },

        # Cloud & DevOps
        "Docker": {
            "title": "Docker for Developers: Containerization & Compose",
            "platform": "Udemy (Bret Fisher)",
            "duration_weeks": 4,
            "level": "Beginner",
            "project": "Multi-Container Microservices Architecture with Healthchecks & Volumes",
            "certification": "Docker Certified Associate (DCA)"
        },
        "Kubernetes": {
            "title": "Certified Kubernetes Administrator (CKA) Mastery",
            "platform": "Linux Foundation / KodeKloud",
            "duration_weeks": 8,
            "level": "Advanced",
            "project": "Deploy High-Availability Cluster with Ingress, Auto-scaling & HPA",
            "certification": "Certified Kubernetes Application Developer (CKAD)"
        },
        "Terraform": {
            "title": "HashiCorp Certified: Terraform Associate",
            "platform": "Udemy / KodeKloud",
            "duration_weeks": 5,
            "level": "Intermediate",
            "project": "Automated Multi-Region Cloud VPC & Kubernetes Cluster Provisioning",
            "certification": "HashiCorp Certified: Terraform Associate (003)"
        },
        "CI/CD": {
            "title": "GitHub Actions & GitLab CI/CD for Modern DevOps",
            "platform": "Udemy / Coursera",
            "duration_weeks": 3,
            "level": "Intermediate",
            "project": "Automated Lint, Test, Security Scan, and Multi-Environment Deployment",
            "certification": "GitHub Actions Certification"
        },
        "AWS": {
            "title": "AWS Certified Solutions Architect Associate",
            "platform": "Coursera / A Cloud Guru",
            "duration_weeks": 8,
            "level": "Intermediate",
            "project": "Serverless Event-Driven Processing System with Lambda, SQS & DynamoDB",
            "certification": "AWS Certified Solutions Architect - Associate (SAA-C03)"
        },
        "Linux": {
            "title": "Linux Administration Fundamentals & Bash Shell Scripting",
            "platform": "edX (Linux Foundation)",
            "duration_weeks": 4,
            "level": "Beginner",
            "project": "Automated Server Health Monitoring, Log Rotation & Alerting Script",
            "certification": "Red Hat Certified System Administrator (RHCSA)"
        },

        # Cybersecurity
        "Network Security": {
            "title": "Network Security & Packet Analysis Deep Dive",
            "platform": "Coursera (Google Cybersecurity Certificate)",
            "duration_weeks": 6,
            "level": "Beginner",
            "project": "Intrusion Detection System Ruleset & Network Traffic Analyzer",
            "certification": "CompTIA Security+ (SY0-701)"
        },
        "Penetration Testing": {
            "title": "Practical Ethical Hacking & Web Application Penetration Testing",
            "platform": "TCM Security / TryHackMe",
            "duration_weeks": 8,
            "level": "Advanced",
            "project": "Vulnerability Assessment and Exploit Demonstration on Sandboxed Lab",
            "certification": "Certified Ethical Hacker (CEH) / PNPT"
        },
        "SIEM": {
            "title": "Splunk & SIEM Threat Detection Architecture",
            "platform": "Coursera / Splunk Training",
            "duration_weeks": 5,
            "level": "Intermediate",
            "project": "SOC Dashboard for Real-Time Brute-force & Ransomware Detection",
            "certification": "Splunk Core Certified Power User"
        },
        "OWASP Top 10": {
            "title": "Web Application Security & OWASP Top 10 Defense",
            "platform": "PortSwigger Web Security Academy",
            "duration_weeks": 4,
            "level": "Intermediate",
            "project": "Secure Code Audit and Remediation on Insecure Banking App",
            "certification": "Certified Web Application Security Specialist"
        },

        # Mobile
        "Flutter": {
            "title": "Flutter & Dart - The Complete Guide (2024)",
            "platform": "Udemy (Academind)",
            "duration_weeks": 6,
            "level": "Intermediate",
            "project": "Cross-Platform Fitness Tracking App with Cloud Sync & Charts",
            "certification": "Flutter Certified Application Developer"
        },
        "Kotlin": {
            "title": "Android App Development with Kotlin & Jetpack Compose",
            "platform": "Google Developers / Udacity",
            "duration_weeks": 6,
            "level": "Intermediate",
            "project": "Material 3 News & Podcast App with Room Offline Database",
            "certification": "Google Associate Android Developer"
        },
        "Swift": {
            "title": "iOS 17 & Swift - The Complete iOS App Development Bootcamp",
            "platform": "Udemy (Dr. Angela Yu)",
            "duration_weeks": 8,
            "level": "Intermediate",
            "project": "SwiftUI Social Networking App with CoreLocation & WidgetKit",
            "certification": "App Development with Swift Certified User"
        },

        # Data Engineering
        "SQL": {
            "title": "Advanced SQL for Data Engineers & Analysts",
            "platform": "Coursera (UC Davis) / LeetCode Database",
            "duration_weeks": 4,
            "level": "Beginner",
            "project": "Complex Analytical Data Warehouse Modeling & Window Functions",
            "certification": "PostgreSQL Professional Certified Developer"
        },
        "Apache Spark": {
            "title": "Taming Big Data with Apache Spark & Python (PySpark)",
            "platform": "Udemy (Frank Kane) / Databricks Academy",
            "duration_weeks": 6,
            "level": "Advanced",
            "project": "Streaming Analytics Pipeline processing 100k IoT messages/sec",
            "certification": "Databricks Certified Associate Developer for Apache Spark"
        },
        "Airflow": {
            "title": "Apache Airflow: The Hands-On Guide for Data Engineers",
            "platform": "Astronomer Academy / Udemy",
            "duration_weeks": 4,
            "level": "Intermediate",
            "project": "Orchestrated Multi-Source ETL Pipeline with Slack Error Alerts",
            "certification": "Astronomer Certified DAG Author"
        },
        "Snowflake": {
            "title": "Snowflake Masterclass: Complete Cloud Data Warehouse",
            "platform": "Coursera / Snowflake Hands-on",
            "duration_weeks": 4,
            "level": "Intermediate",
            "project": "Zero-Copy Clone Data Architecture with Role-Based Access Controls",
            "certification": "Snowflake SnowPro Core Certification"
        },

        # Business Intelligence
        "Tableau": {
            "title": "Tableau Desktop Specialist & Data Storytelling",
            "platform": "Coursera (UC Davis) / Tableau Academy",
            "duration_weeks": 4,
            "level": "Beginner",
            "project": "Executive Sales & Operational Performance KPI Interactive Dashboard",
            "certification": "Tableau Desktop Specialist"
        },
        "Power BI": {
            "title": "Microsoft Power BI Data Analyst (PL-300) Prep",
            "platform": "Microsoft Learn / Coursera",
            "duration_weeks": 5,
            "level": "Intermediate",
            "project": "Financial Forecast Model with DAX Measures & Automated Refresh",
            "certification": "Microsoft Certified: Power BI Data Analyst (PL-300)"
        },
        "Data Visualization": {
            "title": "Data Visualization & Communication with Storytelling",
            "platform": "edX / Harvard Online",
            "duration_weeks": 3,
            "level": "Beginner",
            "project": "Public Sector Impact Analysis Report with Interactive Visuals",
            "certification": "Storytelling with Data Certificate"
        },

        # Embedded & IoT
        "C++": {
            "title": "Modern C++ Programming (C++17 / C++20)",
            "platform": "Coursera / Udemy",
            "duration_weeks": 6,
            "level": "Intermediate",
            "project": "High-Performance Concurrency Engine with Smart Pointers & Templates",
            "certification": "C++ Certified Associate Programmer (CPA)"
        },
        "Microcontrollers": {
            "title": "Embedded Systems Programming: ARM Cortex-M & STM32",
            "platform": "edX (UT Austin) / FastBit Embedded",
            "duration_weeks": 8,
            "level": "Intermediate",
            "project": "I2C/SPI Sensor Driver with Interrupt-Driven Bare-Metal Firmware",
            "certification": "Embedded Systems Professional Certification"
        },
        "RTOS": {
            "title": "Mastering RTOS: Hands-On FreeRTOS with STM32",
            "platform": "Udemy (FastBit)",
            "duration_weeks": 6,
            "level": "Advanced",
            "project": "Multi-Tasking Smart Home Gateway with Mutexes & Queue Management",
            "certification": "Real-Time Embedded Specialist"
        },

        # General / Soft Skills
        "Problem Solving": {
            "title": "Algorithms and Data Structures Masterclass",
            "platform": "Coursera (Princeton) / LeetCode",
            "duration_weeks": 6,
            "level": "Intermediate",
            "project": "Custom Graph Pathfinding & Optimization Algorithm Library",
            "certification": "Competitive Programmer Certificate"
        },
        "Agile & Scrum": {
            "title": "Applied Scrum for Agile Project Management",
            "platform": "Coursera (University of Maryland)",
            "duration_weeks": 2,
            "level": "Beginner",
            "project": "Sprint Planning, Backlog Refinement & Burndown Chart Setup in Jira",
            "certification": "Scrum Alliance Certified ScrumMaster (CSM)"
        }
    }
    return catalog


# -----------------------------------------------------------------------------
# 3. INTERN PROFILES GENERATOR
# -----------------------------------------------------------------------------
FIRST_NAMES = [
    "Aarav", "Aditi", "Alexander", "Amara", "Ananya", "Benjamin", "Chloe", "Daniel",
    "David", "Elena", "Emily", "Ethan", "Fatima", "Gabriel", "Grace", "Hannah",
    "Ibrahim", "Isabella", "Jack", "James", "Jasmine", "Jin", "Kavya", "Liam",
    "Lucas", "Maya", "Michael", "Noah", "Olivia", "Priya", "Rahul", "Rohan",
    "Samantha", "Sara", "Sophia", "Tariq", "Vikram", "William", "Yuki", "Zaid",
    "Carlos", "Mei", "Lars", "Chiara", "Arjun", "Zara", "Dev", "Nadia", "Siddharth", "Fatou"
]

LAST_NAMES = [
    "Sharma", "Patel", "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
    "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee",
    "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis",
    "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Torres", "Nguyen",
    "Hill", "Flores", "Green", "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell"
]

UNIVERSITIES = [
    "Stanford University", "MIT", "UC Berkeley", "Carnegie Mellon University",
    "Georgia Tech", "University of Washington", "University of Illinois Urbana-Champaign",
    "University of Texas at Austin", "University of Michigan", "Cornell University",
    "University of Toronto", "Imperial College London", "National University of Singapore",
    "IIT Bombay", "IIT Delhi", "BITS Pilani", "ETH Zurich", "Technical University of Munich"
]

DEGREES = [
    "B.S. in Computer Science", "B.S. in Software Engineering", "B.S. in Data Science",
    "B.S. in Electrical & Computer Engineering", "B.S. in Information Systems",
    "M.S. in Computer Science", "M.S. in Artificial Intelligence", "M.S. in Data Analytics"
]

def generate_interns(count: int = 320) -> pd.DataFrame:
    records = []
    course_cat = build_course_catalog()
    all_known_skills = list(course_cat.keys())

    domain_keys = list(DOMAINS.keys())

    for i in range(1, count + 1):
        domain = random.choice(domain_keys)
        dom_info = DOMAINS[domain]
        role = random.choice(dom_info["roles"])
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}{random.randint(10, 99)}@example.edu"
        degree = random.choice(DEGREES)
        university = random.choice(UNIVERSITIES)
        grad_year = random.choice([2024, 2025, 2026])
        exp_years = round(random.choice([0.0, 0.5, 1.0, 1.5, 2.0]), 1)

        # Intern skill selection: Select 3-6 core skills, 1-3 advanced skills, 1-3 tools, 1-2 soft skills
        num_core = random.randint(3, min(6, len(dom_info["core_skills"])))
        num_adv = random.randint(0, min(3, len(dom_info["advanced_skills"])))
        num_tools = random.randint(1, min(3, len(dom_info["tools"])))
        num_soft = random.randint(1, 3)

        chosen_core = random.sample(dom_info["core_skills"], num_core)
        chosen_adv = random.sample(dom_info["advanced_skills"], num_adv) if num_adv > 0 else []
        chosen_tools = random.sample(dom_info["tools"], num_tools)
        chosen_soft = random.sample(SOFT_SKILLS, num_soft)

        # Sometimes cross-domain skill (e.g. Python, Git, SQL, Docker)
        bonus_skills = []
        if random.random() < 0.6 and "Git" not in chosen_tools:
            bonus_skills.append("Git")
        if random.random() < 0.4 and "Python" not in chosen_core:
            bonus_skills.append("Python")
        if random.random() < 0.3 and "Docker" not in chosen_tools:
            bonus_skills.append("Docker")

        all_intern_skills = list(dict.fromkeys(chosen_core + chosen_adv + chosen_tools + chosen_soft + bonus_skills))

        # Assign proficiency scores (1 to 5)
        proficiencies = {}
        for s in all_intern_skills:
            if s in chosen_core:
                proficiencies[s] = random.choice([3, 4, 4, 5])
            elif s in chosen_adv:
                proficiencies[s] = random.choice([2, 3, 3, 4])
            elif s in chosen_tools:
                proficiencies[s] = random.choice([2, 3, 4])
            else:
                proficiencies[s] = random.choice([3, 4])

        # Random certifications (0 to 2)
        possible_certs = [
            f"{s} Certified Associate" for s in all_intern_skills if random.random() < 0.25
        ]
        certs = possible_certs[:2]

        # Bio summary
        skills_str = ", ".join(all_intern_skills[:6])
        bio = f"{degree} candidate at {university} passionate about {domain.lower()}. Proficient in {skills_str} with hands-on academic and project experience. Seeking a {role} internship."

        records.append({
            "intern_id": f"INT-{1000 + i}",
            "name": name,
            "email": email,
            "university": university,
            "degree": degree,
            "graduation_year": grad_year,
            "target_domain": domain,
            "target_role": role,
            "experience_years": exp_years,
            "skills": ", ".join(all_intern_skills),
            "skill_count": len(all_intern_skills),
            "proficiencies_json": json.dumps(proficiencies),
            "certifications": ", ".join(certs) if certs else "None",
            "bio": bio
        })

    return pd.DataFrame(records)


# -----------------------------------------------------------------------------
# 4. INDUSTRY JOB DESCRIPTIONS GENERATOR
# -----------------------------------------------------------------------------
TECH_COMPANIES = [
    {"name": "Apex Cloud Systems", "sector": "Cloud Infrastructure", "locations": ["San Francisco, CA", "Seattle, WA", "Remote"]},
    {"name": "NeuralByte AI", "sector": "Artificial Intelligence", "locations": ["New York, NY", "San Jose, CA", "Boston, MA"]},
    {"name": "DataSphere Analytics", "sector": "Big Data & Analytics", "locations": ["Austin, TX", "Chicago, IL", "Remote"]},
    {"name": "CipherShield Cybersecurity", "sector": "Cybersecurity", "locations": ["Washington, DC", "Reston, VA", "Dallas, TX"]},
    {"name": "NovaPay Financial", "sector": "Fintech", "locations": ["New York, NY", "London, UK", "San Francisco, CA"]},
    {"name": "PulseHealth Technologies", "sector": "HealthTech", "locations": ["Boston, MA", "San Diego, CA", "Remote"]},
    {"name": "OmniCommerce Platforms", "sector": "E-Commerce / SaaS", "locations": ["Seattle, WA", "Denver, CO", "Atlanta, GA"]},
    {"name": "RoboMotion Dynamics", "sector": "Robotics & IoT", "locations": ["Pittsburgh, PA", "Detroit, MI", "Sunnyvale, CA"]},
    {"name": "StreamLine Interactive", "sector": "Digital Media & Gaming", "locations": ["Los Angeles, CA", "Vancouver, BC", "Austin, TX"]},
    {"name": "QuantumScale Labs", "sector": "Enterprise Software", "locations": ["Toronto, ON", "New York, NY", "Remote"]}
]

SALARY_RANGES = {
    "Entry-Level": "$70,000 - $95,000",
    "Junior": "$85,000 - $115,000",
    "Mid-Level": "$110,000 - $145,000"
}

def generate_jobs(count: int = 600) -> pd.DataFrame:
    records = []
    domain_keys = list(DOMAINS.keys())

    for i in range(1, count + 1):
        domain = random.choice(domain_keys)
        dom_info = DOMAINS[domain]
        company_obj = random.choice(TECH_COMPANIES)
        company = company_obj["name"]
        sector = company_obj["sector"]
        location = random.choice(company_obj["locations"])
        exp_level = random.choices(["Entry-Level", "Junior", "Mid-Level"], weights=[0.45, 0.40, 0.15])[0]
        role_base = random.choice(dom_info["roles"])

        if exp_level == "Entry-Level":
            title = f"Associate {role_base}" if "Intern" not in role_base else role_base
        elif exp_level == "Junior":
            title = f"Junior {role_base}" if "Junior" not in role_base else role_base
        else:
            title = f"{role_base}"

        # Select required skills (4-7) and preferred skills (2-4)
        req_core = random.sample(dom_info["core_skills"], min(random.randint(3, 5), len(dom_info["core_skills"])))
        req_tools = random.sample(dom_info["tools"], min(random.randint(1, 3), len(dom_info["tools"])))
        req_soft = random.sample(SOFT_SKILLS, min(random.randint(1, 2), len(SOFT_SKILLS)))
        required_skills = list(dict.fromkeys(req_core + req_tools + req_soft))

        avail_adv = [s for s in dom_info["advanced_skills"] if s not in required_skills]
        avail_tools = [s for s in dom_info["tools"] if s not in required_skills]
        pref_adv = random.sample(avail_adv, min(random.randint(2, 4), len(avail_adv))) if avail_adv else []
        pref_tools = random.sample(avail_tools, min(random.randint(1, 2), len(avail_tools))) if avail_tools else []
        preferred_skills = list(dict.fromkeys(pref_adv + pref_tools))

        tools_all = list(dict.fromkeys(req_tools + pref_tools))

        salary = SALARY_RANGES[exp_level]

        # Detailed Job Description Text
        req_str = ", ".join(required_skills)
        pref_str = ", ".join(preferred_skills)
        tools_str = ", ".join(tools_all)

        description = (
            f"{company} is seeking a motivated {title} to join our {sector} engineering team in {location}. "
            f"In this role, you will collaborate on designing, developing, and deploying mission-critical solutions in {domain}. "
            f"Key responsibilities include writing robust, maintainable code, actively participating in code reviews, optimizing system performance, "
            f"and working in an agile environment. "
            f"Required technical proficiencies: {req_str}. "
            f"Preferred qualifications and bonus skills: {pref_str}. "
            f"Key tools and environments: {tools_str}."
        )

        responsibilities = (
            f"1. Design, test, and implement features aligned with {domain} architecture standards.\n"
            f"2. Utilize tools such as {tools_str} for continuous integration, monitoring, and quality assurance.\n"
            f"3. Partner with senior engineers and product managers to translate product specifications into production-grade systems.\n"
            f"4. Troubleshoot and debug complex technical bottlenecks and ensure data security best practices."
        )

        qualifications = (
            f"- Bachelor's or Master's in Computer Science, Data Science, Software Engineering, or related technical field.\n"
            f"- Demonstrated hands-on competence with {', '.join(required_skills[:4])}.\n"
            f"- Strong grasp of {', '.join(SOFT_SKILLS[:3])} in a collaborative sprint framework.\n"
            f"- Familiarity with {', '.join(preferred_skills[:3]) if preferred_skills else 'cloud microservices'} is a strong plus."
        )

        records.append({
            "job_id": f"JOB-{2000 + i}",
            "job_title": title,
            "company": company,
            "sector": sector,
            "location": location,
            "domain": domain,
            "experience_level": exp_level,
            "required_skills": ", ".join(required_skills),
            "preferred_skills": ", ".join(preferred_skills),
            "tools_technologies": ", ".join(tools_all),
            "salary_range": salary,
            "job_description": description,
            "responsibilities": responsibilities,
            "qualifications": qualifications
        })

    return pd.DataFrame(records)


# -----------------------------------------------------------------------------
# 5. SKILLS TAXONOMY JSON GENERATOR
# -----------------------------------------------------------------------------
def build_skills_taxonomy() -> Dict[str, Any]:
    taxonomy = {}
    categories = {
        "Programming Languages": ["Python", "JavaScript", "TypeScript", "C", "C++", "Kotlin", "Swift", "Dart", "SQL", "Bash Scripting"],
        "Frameworks & Libraries": ["React", "Node.js", "Express.js", "Next.js", "Flutter", "React Native", "TensorFlow", "PyTorch", "scikit-learn", "Pandas", "NumPy", "Hugging Face", "LangChain", "FastAPI", "Redux", "GraphQL"],
        "Cloud & DevOps": ["Docker", "Kubernetes", "CI/CD", "Terraform", "AWS", "Azure", "GCP", "Linux", "Ansible", "Helm", "Prometheus", "Grafana", "MLflow", "MLOps"],
        "Databases & Big Data": ["PostgreSQL", "MongoDB", "Redis", "Apache Spark", "Apache Kafka", "Airflow", "Snowflake", "dbt", "Hadoop", "PySpark", "Data Warehousing", "ETL"],
        "Cybersecurity & Networking": ["Network Security", "Cryptography", "Penetration Testing", "SIEM", "Incident Response", "OWASP Top 10", "Firewalls", "TCP/IP", "Vulnerability Assessment", "Wireshark", "Burp Suite", "Splunk"],
        "Embedded & Hardware": ["Microcontrollers", "RTOS", "Embedded C", "UART/SPI/I2C Protocols", "FreeRTOS", "Embedded Linux", "BLE / Zigbee", "MQTT", "ARM Architecture"],
        "Business Intelligence & Analytics": ["Tableau", "Power BI", "Data Visualization", "Exploratory Data Analysis", "A/B Testing", "Cohort Analysis", "DAX", "Business Metrics", "Excel & Spreadsheets"],
        "Soft Skills & Methodologies": SOFT_SKILLS
    }

    # Map each skill to domain, category, difficulty
    for cat_name, skills in categories.items():
        for skill in skills:
            # Find primary domain
            primary_dom = "General Tech"
            for d_name, d_val in DOMAINS.items():
                if skill in d_val["core_skills"] or skill in d_val["advanced_skills"] or skill in d_val["tools"]:
                    primary_dom = d_name
                    break

            diff = "Intermediate"
            if skill in ["Python", "SQL", "HTML5", "CSS3", "Git", "Linux", "Excel & Spreadsheets"] + SOFT_SKILLS:
                diff = "Beginner"
            elif skill in ["Kubernetes", "Terraform", "Deep Learning", "Transformers", "Large Language Models", "Apache Spark", "RTOS", "Penetration Testing"]:
                diff = "Advanced"

            taxonomy[skill] = {
                "name": skill,
                "category": cat_name,
                "domain": primary_dom,
                "difficulty": diff
            }

    return taxonomy


def main():
    print("=================================================================")
    print("Generating Datasets for Intern Skills & Industry Demand Analysis")
    print("=================================================================")

    # 1. Course Catalog
    courses = build_course_catalog()
    catalog_path = os.path.join(DATA_DIR, "course_catalog.json")
    with open(catalog_path, "w", encoding="utf-8") as f:
        json.dump(courses, f, indent=2)
    print(f"Saved Course Catalog: {catalog_path} ({len(courses)} courses)")

    # 2. Skills Taxonomy
    taxonomy = build_skills_taxonomy()
    taxonomy_path = os.path.join(DATA_DIR, "skills_taxonomy.json")
    with open(taxonomy_path, "w", encoding="utf-8") as f:
        json.dump(taxonomy, f, indent=2)
    print(f"Saved Skills Taxonomy: {taxonomy_path} ({len(taxonomy)} skills)")

    # 3. Interns Skills CSV
    interns_df = generate_interns(count=350)
    interns_path = os.path.join(DATA_DIR, "interns_skills.csv")
    interns_df.to_csv(interns_path, index=False)
    print(f"Saved Interns Database: {interns_path} ({len(interns_df)} records)")

    # 4. Industry Jobs CSV
    jobs_df = generate_jobs(count=650)
    jobs_path = os.path.join(DATA_DIR, "industry_jobs.csv")
    jobs_df.to_csv(jobs_path, index=False)
    print(f"Saved Industry Jobs Database: {jobs_path} ({len(jobs_df)} postings)")

    print("\nDataset generation completed successfully!\n")

if __name__ == "__main__":
    main()
