# Internship Project Report: Intern Skills Analysis & Industry Demand Gap Identification

**Author / Intern**: AI & Machine Learning Engineering Intern  
**Project Domain**: Natural Language Processing (NLP), Unsupervised Clustering (K-Means), Educational Recommender Systems  
**Date**: September 2026  

---

## Executive Summary

The transition from academic curricula to industry roles presents a persistent challenge: the divergence between skills taught in universities and the rapidly evolving demands of technical employers. This project develops an end-to-end Machine Learning and Natural Language Processing (NLP) system designed to:
1. Process and vectorize industry job postings and intern candidate skill profiles.
2. Uncover natural career archetypes and technical domain clusters using **TF-IDF Feature Extraction** and **K-Means Clustering**.
3. Quantify skill deficits (missing mandatory skills, preferred bonuses, and proficiency gaps) through multi-tiered semantic and set-based matching.
4. Synthesize personalized, 12-week structured upskilling curricula (incorporating courses, capstone projects, and certifications) to systematically close identified competency gaps.
5. Provide an interactive, responsive analytics dashboard for interns, educators, and talent acquisition teams.

---

## 1. Problem Formulation & Objectives

### 1.1 Problem Statement
Entry-level tech applicants frequently encounter rejection not due to a lack of fundamental problem-solving capability, but due to targeted gaps in production-grade frameworks, tools, and domain-specific practices (such as Docker, Kubernetes, CI/CD, MLOps, Next.js, and SIEM tools). Without automated diagnostics, interns struggle to prioritize what to learn next, leading to inefficient upskilling.

### 1.2 Core Objectives
- **Data Ingestion & Synthesis**: Create comprehensive, realistic databases reflecting current hiring standards across 8 primary technical domains.
- **NLP Vectorization**: Normalize technical terminology and compute high-dimensional feature representations using sublinear TF-IDF.
- **Unsupervised Market Clustering**: Group 650+ job postings into distinct career archetypes with $k=8$ K-Means clustering and 2D PCA dimensionality reduction.
- **Skill Gap & Readiness Quantification**: Calculate individual and macro-level competency deficits with semantic cosine similarity and granular set-difference matching.
- **Automated Curriculum Recommendation**: Generate 3-phase, 12-week roadmaps linking every deficiency to vetted courses, capstones, and certifications.

---

## 2. Methodology & Technical Architecture

### 2.1 Data Architecture
- **Intern Database (`interns_skills.csv`)**: 350 candidate records with attributes:
  - `intern_id`, `name`, `email`, `university`, `degree`, `target_domain`, `target_role`, `experience_years`, `skills`, `proficiencies_json` (1-5 Likert scale), `certifications`, `bio`.
- **Industry Jobs Database (`industry_jobs.csv`)**: 650 job postings with attributes:
  - `job_id`, `job_title`, `company`, `sector`, `location`, `domain`, `experience_level`, `required_skills`, `preferred_skills`, `tools_technologies`, `salary_range`, `job_description`.
- **Skills Taxonomy (`skills_taxonomy.json`)**: 92 categorized tech skills organized by domain, category, and difficulty level.
- **Course Catalog (`course_catalog.json`)**: 39 curated courses with duration (weeks), project specifications, and certifications.

### 2.2 Text Preprocessing & TF-IDF Vectorization
Standard NLP tokenizers often mangle technical strings (e.g. converting `C++` into `C`, `Node.js` into `Node js`, or `CI/CD` into `CI CD`). A custom preprocessing pipeline (`clean_tech_text`) handles token normalization:
$$\text{Normalize: } C++ \to \text{"cplusplus"}, \quad \text{Node.js} \to \text{"nodejs"}, \quad \text{CI/CD} \to \text{"cicd"}$$

Sublinear TF scaling is applied:
$$\text{TF-IDF}(t, d) = (1 + \log(\text{TF}(t, d))) \times \log\left(\frac{1 + N}{1 + \text{DF}(t)}\right)$$
with unigram and bigram extraction ($n \in [1, 2]$) and 1,200 maximum features.

### 2.3 K-Means Clustering & Centroid Profiling
K-Means partitions the job descriptions matrix $X \in \mathbb{R}^{650 \times 1200}$ into $k=8$ clusters by minimizing within-cluster sum-of-squares (inertia):
$$\operatorname*{arg\,min}_{\mathbf{S}} \sum_{i=1}^{k} \sum_{\mathbf{x} \in S_i} \|\mathbf{x} - \boldsymbol{\mu}_i\|^2$$

Centroid feature weights are analyzed to extract top TF-IDF keywords that automatically characterize each cluster.

### 2.4 Dimensionality Reduction (2D PCA)
To project high-dimensional TF-IDF vectors into a 2D plane for visual cluster exploration:
$$\mathbf{z}_i = W^T (\mathbf{x}_i - \bar{\mathbf{x}})$$
where $W \in \mathbb{R}^{1200 \times 2}$ consists of the eigenvectors corresponding to the top two eigenvalues of the covariance matrix.

### 2.5 Skill Gap Formulation & Readiness Scoring
For an intern vector $\mathbf{v}_{\text{intern}}$ and target job vector $\mathbf{v}_{\text{job}}$:
1. **Cosine Similarity**:
   $$\text{Sim}(\mathbf{v}_{\text{intern}}, \mathbf{v}_{\text{job}}) = \frac{\mathbf{v}_{\text{intern}} \cdot \mathbf{v}_{\text{job}}}{\|\mathbf{v}_{\text{intern}}\| \|\mathbf{v}_{\text{job}}\|}$$
2. **Required Skill Match Ratio**:
   $$R_{\text{req}} = \frac{|\mathcal{S}_{\text{intern}} \cap \mathcal{S}_{\text{job, req}}|}{|\mathcal{S}_{\text{job, req}}|}$$
3. **Preferred Skill Match Ratio**:
   $$R_{\text{pref}} = \frac{|\mathcal{S}_{\text{intern}} \cap \mathcal{S}_{\text{job, pref}}|}{|\mathcal{S}_{\text{job, pref}}|}$$
4. **Composite Readiness Score**:
   $$\text{Readiness} = \min\left(98\%, \max\left(10\%, \left[0.40 \cdot \text{Sim} + 0.45 \cdot R_{\text{req}} + 0.15 \cdot R_{\text{pref}}\right] \times 100\right)\right)$$

---

## 3. Discovered Industry Clusters & Findings

| Cluster ID | Cluster Name | Dominant Domain | Job Count | Key Demanded Skills | Top TF-IDF Terms |
| :---: | :--- | :--- | :---: | :--- | :--- |
| **0** | Cybersecurity & Network Defense | Cybersecurity | 78 | Cryptography, TCP/IP, Linux, Network Security | network, security, defense, packet |
| **1** | Business Intelligence & Analytics | BI & Analytics | 93 | SQL, Tableau, Statistics, Power BI, EDA | business, powerbi, tableau, analytics |
| **2** | Mobile Application Development | Mobile App Dev | 103 | State Management, Dart, Mobile UI, Swift, REST | mobile, application, gradle, figma |
| **3** | Data Engineering & Big Data | Data Engineering | 78 | ETL, Git, Data Pipelines, Linux, SQL, Spark | data, kafka, big data, pipeline |
| **4** | AI & Machine Learning | AI & ML | 81 | Machine Learning, Data Analysis, Python, PyTorch | learning, machine, sagemaker, ai |
| **5** | Cloud Architecture & DevOps | Cloud & DevOps | 78 | CI/CD, Docker, Cloud, Kubernetes, Bash | cloud, devops, terraform, jenkins |
| **6** | Embedded Systems & IoT | Embedded & IoT | 58 | RTOS, UART/SPI/I2C, Microcontrollers, C++ | embedded, systems, iot, analyzer |
| **7** | Full Stack Web Development | Full Stack Web | 81 | SQL, HTML5, TypeScript, Git, React, Node.js | web, full stack, vite, express |

### 3.1 Macro Supply vs Demand Deficit Analysis
The analysis revealed the largest market deficits between industry job requirements and intern skill supply:
1. **Containerization & Orchestration (Docker / Kubernetes)**: +34.2% Deficit
2. **Infrastructure as Code & CI/CD**: +28.5% Deficit
3. **Applied MLOps & Large Language Models**: +26.8% Deficit
4. **Cloud Data Warehouses (Snowflake / Airflow)**: +22.4% Deficit
5. **Modern Type-Safe Full Stack (Next.js / TypeScript)**: +19.7% Deficit

---

## 4. Personalized 12-Week Upskilling Roadmap Design

The system structures remediation into 3 sequential phases:
- **Phase 1: Core Fundamentals & Critical Deficiencies (Weeks 1-4)**: Focuses on mandatory missing prerequisites required for technical screening.
- **Phase 2: Applied Frameworks & Proficiency Upgrades (Weeks 5-8)**: Closes proficiency gaps on tools the intern has encountered but not mastered.
- **Phase 3: Production Projects, Specialization & Certifications (Weeks 9-12)**: Completes resume-ready capstone projects and formal industry certifications.

---

## 5. Verification & Testing

- **Automated Unit & Integration Tests**: 12 comprehensive test cases validating preprocessing, TF-IDF vectorization, K-Means clustering, PCA coordinates, readiness score bounds, custom simulator processing, and all 7 REST API endpoints passed in **0.818s**.
- **Interactive Web Verification**: Tested on local server (`http://127.0.0.1:5000`) with responsive Chart.js radar charts, 2D PCA scatter plots, intern modal workflows, and live simulator inputs.

---

## 6. Conclusion & Recommendations

The developed system provides an end-to-end, automated solution for bridging the gap between university graduates and industry talent demands. By combining NLP TF-IDF vectorization, K-Means clustering, and structured training recommendations, the platform enables:
1. **Interns** to identify specific skill deficits and follow actionable 12-week study plans.
2. **Educators & Universities** to adjust curricula to prioritize high-deficit technologies (Cloud, CI/CD, MLOps, Containerization).
3. **Recruiters & Mentors** to rapidly assess intern readiness and personalize onboarding.
