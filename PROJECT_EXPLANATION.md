# AI-Based Skill Gap Prediction & Learning Recommendation System

## Complete Project Explanation

**Project Code:** MCA_MP_69  
**Institution:** Presidency University  
**Repository:** [github.com/Raghavendra0348/Backend](https://github.com/Raghavendra0348/Backend)  
**Last Updated:** September 2026

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Problem Statement](#2-problem-statement)
3. [System Architecture](#3-system-architecture)
4. [Technology Stack](#4-technology-stack)
5. [Repository Structure](#5-repository-structure)
6. [Database Design](#6-database-design)
7. [Core Modules & Services](#7-core-modules--services)
8. [API Layer](#8-api-layer)
9. [Machine Learning Pipeline](#9-machine-learning-pipeline)
10. [Data Sources & Ingestion](#10-data-sources--ingestion)
11. [Authentication & Security](#11-authentication--security)
12. [Caching Strategy](#12-caching-strategy)
13. [Frontend (Templates)](#13-frontend-templates)
14. [Testing](#14-testing)
15. [Setup & Deployment](#15-setup--deployment)
16. [Data Flow Walkthrough](#16-data-flow-walkthrough)
17. [Key Algorithms & Formulas](#17-key-algorithms--formulas)
18. [Future Development Roadmap](#18-future-development-roadmap)

---

## 1. Project Overview

This project is an **AI-powered backend system** that predicts skill gaps for students/professionals and recommends personalized learning paths to bridge those gaps. It sits at the intersection of:

- **Career Readiness Assessment** — How prepared is a student for a specific IT job role?
- **Skill Gap Analysis** — Which skills does the student lack, and how severe is each gap?
- **Intelligent Recommendations** — Which courses will most efficiently close those gaps?
- **Personalized Learning Paths** — In what order should the student learn, and how long will it take?

The system uses real-world occupational taxonomies (**ESCO** from the European Commission, **O*NET** from the U.S. Department of Labor) and a curated **Coursera course catalog** to provide grounded, actionable recommendations rather than generic advice.

---

## 2. Problem Statement

### The Challenge

Students finishing academic programs often face a disconnect between their academic curriculum and the skill requirements of industry IT roles. Key issues include:

1. **Students don't know what they don't know** — They may be unaware of critical skills required for their target career
2. **Self-assessment is unreliable** — Students tend to overestimate or underestimate their own skill levels
3. **Information overload** — Thousands of online courses exist, but which ones actually matter for a specific career goal?
4. **No structured learning plan** — Even if students identify gaps, they lack a sequenced roadmap to fill them

### The Solution

This backend provides:

| Capability | What It Does |
|---|---|
| **Skill Profiling** | Students register skills (manually or via resume upload) with proficiency ratings |
| **Resume Intelligence** | PDF/DOCX resumes are parsed using NLP to automatically extract skills, projects, and certifications |
| **Gap Detection** | The system compares the student's skill profile against the requirements of target IT job roles |
| **ML Classification** | A trained ML model classifies gap severity (LOW / MEDIUM / HIGH) using features like proficiency, assessments, projects, and certifications |
| **Course Recommendations** | A 6-factor hybrid engine recommends courses from a 3,500+ Coursera catalog, ranked by relevance, difficulty fit, quality, and diversity |
| **Learning Paths** | A phased roadmap (Critical → Core → Polish) with estimated study hours and ordered courses |
| **Progress Tracking** | Students track course completion, retake assessments, and measure improvement over time |
| **Analytics** | Skill growth trends, gap reduction timelines, and role readiness progression |

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                 │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐                      │
│   │ index.html│   │skills.html│  │learning. │   (Jinja2 Templates) │
│   │ Home/Auth │   │Resume/Gap│   │  html    │                      │
│   └────┬─────┘   └────┬─────┘   └────┬─────┘                      │
│        │               │              │                             │
└────────┼───────────────┼──────────────┼─────────────────────────────┘
         │               │              │
         ▼               ▼              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       API LAYER (Flask)                              │
│                                                                     │
│  ┌─────────────────┐  ┌──────────────────────────────────────────┐ │
│  │  Legacy Routes   │  │       v1 API Blueprints                  │ │
│  │  /api/*          │  │  /api/v1/students   /api/v1/skills      │ │
│  │  (routes.py)     │  │  /api/v1/roles      /api/v1/assessments │ │
│  └─────────────────┘  │  /api/v1/resumes     /api/v1/gap-analysis│ │
│                        │  /api/v1/recommend   /api/v1/learning    │ │
│  ┌─────────────────┐  │  /api/v1/analytics                      │ │
│  │  Auth Blueprint  │  └──────────────────────────────────────────┘ │
│  │  /api/auth/*     │                                               │
│  └─────────────────┘                                                │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │              Marshmallow Schema Validation                    │   │
│  │  student_schemas · resume_schemas · gap_schemas · etc.        │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SERVICE LAYER                                  │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐          │
│  │ gap_engine.py │  │recommender.py│  │ resume_parser.py│          │
│  │ Skill Gap     │  │ 6-Factor     │  │ PDF/DOCX → NLP │          │
│  │ Analysis + ML │  │ Hybrid Rec.  │  │ Skill Extraction│          │
│  └──────────────┘  └──────────────┘  └─────────────────┘          │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐          │
│  │role_matcher.py│  │learning_path │  │skill_normalizer │          │
│  │ Match Score   │  │  .py         │  │  .py            │          │
│  │ Readiness %   │  │ Phased Plans │  │ Alias Mapping   │          │
│  └──────────────┘  └──────────────┘  └─────────────────┘          │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐          │
│  │ analytics.py  │  │resume_service│  │ assessment_svc  │          │
│  │ Growth Trends │  │  .py         │  │  .py            │          │
│  └──────────────┘  └──────────────┘  └─────────────────┘          │
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐          │
│  │student_svc.py│  │ skill_svc.py │  │ role_service.py │          │
│  └──────────────┘  └──────────────┘  └─────────────────┘          │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                cache.py (In-Memory TTL Cache)                 │   │
│  │    gap_cache · rec_cache · match_cache · path_cache           │   │
│  └──────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────┬────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DATA / PERSISTENCE LAYER                         │
│                                                                     │
│  ┌──────────────────────┐   ┌──────────────────────────────┐       │
│  │  SQLAlchemy ORM       │   │ Flask-Migrate (Alembic)      │       │
│  │  17 database models   │   │ Versioned schema migrations  │       │
│  └──────────┬───────────┘   └──────────────────────────────┘       │
│             │                                                       │
│             ▼                                                       │
│  ┌──────────────────────┐   ┌──────────────────────────────┐       │
│  │  SQLite (dev default) │   │ MySQL (production target)    │       │
│  │  Zero-config local    │   │ mysql+pymysql driver         │       │
│  └──────────────────────┘   └──────────────────────────────┘       │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │          ML Model (scikit-learn, joblib serialized)           │   │
│  │  Gradient Boosting classifier for gap severity prediction     │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │
┌────────────────────────────────┴────────────────────────────────────┐
│                  EXTERNAL DATA SOURCES                               │
│                                                                     │
│  ┌────────────┐  ┌────────────┐  ┌─────────────┐  ┌────────────┐  │
│  │ ESCO v1.2.1│  │ O*NET v27+ │  │ Coursera    │  │ Student    │  │
│  │ 3,000 roles│  │ Knowledge  │  │ 3,500+      │  │ Profiles   │  │
│  │ 13,800+    │  │ Work       │  │ courses     │  │ with Indian│  │
│  │ skills     │  │ Activities │  │ CSV catalog │  │ names      │  │
│  └────────────┘  └────────────┘  └─────────────┘  └────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 4. Technology Stack

### Backend Framework & Core

| Technology | Purpose | Version |
|---|---|---|
| **Python** | Primary language | 3.12+ |
| **Flask** | Web framework & application factory | >=3.0 |
| **Flask-SQLAlchemy** | ORM for database operations | >=3.1 |
| **Flask-Migrate** | Database schema migrations (Alembic) | >=4.0 |
| **Flask-CORS** | Cross-Origin Resource Sharing | >=4.0 |
| **Flask-JWT-Extended** | JWT token authentication | >=4.6 |

### Machine Learning & Data Science

| Technology | Purpose | Version |
|---|---|---|
| **scikit-learn** | ML model training & inference | >=1.4 |
| **pandas** | Data manipulation & ingestion | >=2.2 |
| **numpy** | Numerical operations | >=1.26 |
| **joblib** | Model serialization/deserialization | >=1.3 |

### Security & Utilities

| Technology | Purpose | Version |
|---|---|---|
| **bcrypt** | Password hashing (salted, slow hash) | >=4.1 |
| **python-dotenv** | Environment variable loading | >=1.0 |
| **cachetools** | In-memory TTL cache | >=5.3 |
| **marshmallow** | Request/response schema validation | >=3.20 |

### Data Processing

| Technology | Purpose | Version |
|---|---|---|
| **pypdf** | PDF resume text extraction | >=5 |
| **python-docx** | DOCX resume text extraction | >=1.1 |
| **openpyxl** | Excel file reading (O*NET data) | >=3.1 |

### Database

| Technology | Purpose |
|---|---|
| **SQLite** | Default development database (zero-config) |
| **MySQL** | Production target (via PyMySQL driver) |

### Testing

| Technology | Purpose | Version |
|---|---|---|
| **pytest** | Test framework | >=8 |
| **pytest-flask** | Flask test client integration | >=1.3 |

---

## 5. Repository Structure

```
Backend/                                    ← Repository root
│
├── AI_Skill_Gap_Backend_Implementation/    ← Main application code
│   ├── app.py                              ← Flask app factory + CLI commands
│   ├── config.py                           ← Configuration (reads .env)
│   ├── models.py                           ← 17 SQLAlchemy database models
│   ├── routes.py                           ← Legacy API routes (/api/)
│   ├── auth.py                             ← JWT authentication + ownership guards
│   ├── extensions.py                       ← Flask extensions (db, migrate)
│   ├── cache.py                            ← In-memory TTL cache (4 caches)
│   │
│   ├── api/                                ← v1 API blueprints (/api/v1/)
│   │   ├── __init__.py                     ← Blueprint aggregation + response envelope
│   │   ├── students.py                     ← Student CRUD + profile management
│   │   ├── skills.py                       ← Skills catalog API
│   │   ├── roles.py                        ← Job roles listing
│   │   ├── assessments.py                  ← Skill assessment scoring
│   │   ├── resumes.py                      ← Resume upload + AI extraction
│   │   ├── gap_analysis.py                 ← Skill gap computation endpoint
│   │   ├── recommendations.py             ← Course recommendation engine
│   │   ├── learning.py                     ← Learning path + progress tracking
│   │   └── analytics.py                    ← Skill growth analytics
│   │
│   ├── services/                           ← Business logic layer
│   │   ├── gap_engine.py                   ← Core skill gap analysis + ML inference
│   │   ├── recommender.py                  ← 6-factor hybrid recommendation engine
│   │   ├── resume_parser.py                ← PDF/DOCX extraction + NLP skill matching
│   │   ├── resume_service.py               ← Resume processing orchestration
│   │   ├── skill_normalizer.py             ← 350+ alias canonicalization engine
│   │   ├── role_matcher.py                 ← Job role readiness scorer
│   │   ├── learning_path.py                ← Phased learning roadmap generator
│   │   ├── analytics.py                    ← Skill progress & trend computation
│   │   ├── assessment_service.py           ← Assessment scoring logic
│   │   ├── student_service.py              ← Student profile operations
│   │   ├── skill_service.py                ← Skill catalog operations
│   │   └── role_service.py                 ← Role data operations
│   │
│   ├── schemas/                            ← Marshmallow request validation
│   │   ├── __init__.py                     ← Schema exports
│   │   ├── student_schemas.py              ← Student input validation
│   │   ├── resume_schemas.py               ← Resume upload validation
│   │   ├── assessment_schemas.py           ← Assessment input validation
│   │   ├── gap_schemas.py                  ← Gap analysis input validation
│   │   └── learning_schemas.py             ← Learning progress validation
│   │
│   ├── data/                               ← Data ingestion scripts
│   │   ├── ingest.py                       ← ESCO, O*NET, Coursera, student ingestion
│   │   └── seed_courses.py                 ← Curated course seeding (91KB of data)
│   │
│   ├── ml/                                 ← Machine learning pipeline
│   │   ├── generate_dataset.py             ← Synthetic training data generator
│   │   ├── train.py                        ← Multi-model training + evaluation
│   │   ├── skill_gap_dataset.csv           ← Generated training dataset
│   │   └── models/                         ← Serialized model + metrics
│   │
│   ├── templates/                          ← Jinja2 HTML frontend
│   │   ├── index.html                      ← Home page (auth, profile, role match)
│   │   ├── skills.html                     ← Skills, resume parser, gap analysis
│   │   └── learning.html                   ← Learning path, recommendations, analytics
│   │
│   ├── tests/                              ← Pytest test suites
│   │   ├── conftest.py                     ← Test fixtures (in-memory SQLite)
│   │   ├── test_api.py                     ← Legacy API endpoint tests
│   │   ├── test_v1_api.py                  ← v1 API endpoint tests
│   │   ├── test_gap_engine.py              ← Gap engine unit tests
│   │   ├── test_recommender.py             ← Recommendation engine tests
│   │   ├── test_resume_parser.py           ← Resume parser tests
│   │   ├── test_skill_normalizer.py        ← Skill normalizer tests
│   │   └── test_onet_ingest.py             ← O*NET ingestion tests
│   │
│   ├── migrations/                         ← Alembic migration scripts
│   ├── storage/                            ← Uploaded file storage
│   ├── requirements.txt                    ← Python dependencies
│   ├── .env.example                        ← Environment variable template
│   └── README.md                           ← Application README
│
├── Dataset/                                ← External datasets
│   ├── esco/                               ← ESCO v1.2.1 classification CSVs
│   ├── onet/                               ← O*NET Knowledge, Activities, Occupations
│   ├── coursera/                           ← 3,500+ course catalog CSV
│   └── students/                           ← Student profile test data
│
├── ESCO dataset - v1.2.1 - .../           ← Legacy ESCO data (backward compat)
│
├── docs/                                   ← Project documentation
│   ├── AI_Skill_Gap_PRD.pdf               ← Product Requirements Document
│   ├── AI_Skill_Gap_Backend_Implementation_Guide.pdf
│   ├── MCA_MP_69.pptx                     ← Presentation
│   └── implementation_plan.md             ← Implementation plan
│
├── AI_Skill_Gap_Backend_Development_Plan.md ← Deep technical improvement plan
├── staged_development_plan.md              ← 11-stage development roadmap
├── WINDOWS_SETUP_GUIDE.md                  ← Windows setup instructions
└── .gitignore
```

---

## 6. Database Design

The system uses **17 SQLAlchemy models** organized into logical domains:

### 6.1 User & Identity

```
┌──────────────────────┐        ┌────────────────────────┐
│       users           │        │       students          │
├──────────────────────┤  1:1   ├────────────────────────┤
│ id (PK)              │◄──────►│ id (PK)                │
│ email (unique)       │        │ name                    │
│ name                 │        │ email (unique)          │
│ password_hash        │        │ course (e.g. MCA)       │
│ role (student/admin) │        │ year                    │
│ student_id (FK)      │        │ target_career           │
│ created_at           │        │ created_at              │
│ last_login           │        │ updated_at              │
└──────────────────────┘        └────────────────────────┘
```

- **`User`** — Authentication account (email, bcrypt password hash, JWT identity)
- **`Student`** — Academic profile (name, course, year, target career)
- Linked 1:1 via `user.student_id`; registration auto-creates both records

### 6.2 Skills & Taxonomy

```
┌──────────────────────┐        ┌────────────────────────┐
│       skills          │        │     student_skills      │
├──────────────────────┤  1:N   ├────────────────────────┤
│ id (PK)              │◄──────►│ id (PK)                │
│ name (unique)        │        │ student_id (FK)         │
│ category             │        │ skill_id (FK)           │
│ description          │        │ proficiency (0-100)     │
│ source (ESCO/O*NET/  │        │ evidence_type           │
│   CANONICAL)         │        │ confidence (0-1)        │
│ source_identifier    │        │ updated_at              │
└──────────────────────┘        └────────────────────────┘
```

- **`Skill`** — Canonical skill entry with source tracking (ESCO URI, O*NET ID, or manually curated)
- **`StudentSkill`** — A student's proficiency in a specific skill (0-100 scale) with evidence type and confidence score

### 6.3 Job Roles & Requirements

```
┌──────────────────────┐        ┌────────────────────────┐
│      job_roles        │        │       job_skills        │
├──────────────────────┤  1:N   ├────────────────────────┤
│ id (PK)              │◄──────►│ id (PK)                │
│ name                 │        │ job_role_id (FK)        │
│ source (ESCO/O*NET/  │        │ skill_id (FK)           │
│   DEMO)              │        │ required_level (0-100)  │
│ source_identifier    │        │ importance (0-1)        │
│ description          │        │ relation_type           │
│ isco_group           │        │   (essential/optional)  │
│ onet_code            │        │ source                  │
└──────────────────────┘        └────────────────────────┘
```

- **`JobRole`** — 15 curated IT roles (Frontend Dev, Backend Dev, Data Scientist, etc.) plus ESCO/O*NET roles
- **`JobSkill`** — Maps each role to its required skills with importance weights and required proficiency levels

### 6.4 Resume & Evidence

```
┌──────────────────────┐   ┌────────────────────────┐   ┌───────────────────────┐
│      resumes          │   │    skill_evidence       │   │  ai_extraction_records│
├──────────────────────┤   ├────────────────────────┤   ├───────────────────────┤
│ id (PK)              │   │ id (PK)                │   │ id (PK)               │
│ student_id (FK)      │   │ student_id (FK)        │   │ student_id (FK)       │
│ file_name            │   │ skill_id (FK)          │   │ source_type           │
│ stored_path          │   │ raw_term               │   │ source_id             │
│ extracted_text       │   │ evidence_type          │   │ model                 │
│ processing_status    │   │ confidence (0-1)       │   │ prompt_version        │
│ created_at           │   │ evidence_span          │   │ latency_ms            │
└──────────────────────┘   │ section                │   │ token_usage           │
                           │ status (pending/       │   │ skills_extracted_count│
                           │   verified/rejected)   │   │ unknown_count         │
                           └────────────────────────┘   └───────────────────────┘
```

- **`Resume`** — Uploaded PDF/DOCX with extracted raw text and processing status
- **`SkillEvidence`** — Granular evidence for each extracted skill (includes context snippet, section location, confidence score)
- **`AIExtractionRecord`** — Audit trail of AI/NLP extraction runs (model version, latency, token usage)

### 6.5 Gap Analysis & Recommendations

```
┌──────────────────────┐   ┌────────────────────────┐   ┌───────────────────────┐
│     skill_gaps        │   │   recommendations      │   │  recommendation_runs  │
├──────────────────────┤   ├────────────────────────┤   ├───────────────────────┤
│ id (PK)              │   │ id (PK)                │   │ id (PK)               │
│ student_id (FK)      │   │ student_id (FK)        │   │ student_id (FK)       │
│ job_role_id (FK)     │   │ skill_id (FK)          │   │ job_role_id (FK)      │
│ skill_id (FK)        │   │ course_id (FK)         │   │ weights_used (JSON)   │
│ current_level        │   │ title                  │   │ total_recommendations │
│ required_level       │   │ url                    │   │ recommendations_      │
│ gap_value            │   │ score                  │   │   snapshot (JSON)     │
│ gap_percent          │   │ reason                 │   │ created_at            │
│ severity (LOW/MED/HI)│   │ created_at             │   └───────────────────────┘
│ priority_score       │   └────────────────────────┘
│ evidence_summary     │
│ evidence_factor      │
│ explanation          │
│ model_version        │
│ created_at           │
└──────────────────────┘
```

- **`SkillGap`** — Computed gap per skill with severity, priority, evidence factor, and human-readable explanation
- **`Recommendation`** — Course recommendations per skill gap
- **`RecommendationRun`** — Snapshot of a recommendation run (reproducibility over time, stores weights used and full JSON snapshot)

### 6.6 Learning & Progress

```
┌──────────────────────┐   ┌────────────────────────┐   ┌───────────────────────┐
│   learning_paths      │   │  learning_path_steps   │   │  learning_progress    │
├──────────────────────┤   ├────────────────────────┤   ├───────────────────────┤
│ id (PK)              │   │ id (PK)                │   │ id (PK)               │
│ student_id (FK)      │   │ path_id (FK)           │   │ student_id (FK)       │
│ job_role_id (FK)     │   │ step_order (1,2,3...)  │   │ course_id (FK)        │
│ total_courses        │   │ course_id (FK)         │   │ skill_id (FK)         │
│ total_hours          │   │ skill_id (FK)          │   │ title                 │
│ match_score_at_gen   │   │ phase (HIGH/MED/LOW)   │   │ status                │
│ created_at           │   │ estimated_hours        │   │ completion (0-100)    │
└──────────────────────┘   └────────────────────────┘   │ updated_at            │
                                                         └───────────────────────┘
```

### 6.7 Other Models

| Model | Purpose |
|---|---|
| **`Assessment`** | Records per-skill test scores with attempt tracking |
| **`Project`** | Student projects with skills used |
| **`Certification`** | Student certifications with issuer and dates |
| **`Reassessment`** | Tracks old → new proficiency levels with improvement delta |
| **`UnknownSkillReview`** | Review queue for terms that can't be mapped to canonical skills |
| **`ImportBatch`** | Tracks every data import run (source, rows, status, errors) |
| **`Course`** | Learning resource with title, provider, difficulty, rating, URL |
| **`CourseSkill`** | Maps courses to skills with relevance score |

---

## 7. Core Modules & Services

### 7.1 Skill Gap Engine (`services/gap_engine.py`)

The heart of the system. Computes the gap between a student's current skills and a target role's requirements.

**How It Works:**

1. Fetches the student's skills (`StudentSkill` records)
2. Fetches the target role's required skills (`JobSkill` records)
3. For each required skill, computes:
   - **Gap** = `max(0, required_level - current_level)`
   - **Gap %** = `gap / required_level x 100`
   - **Priority** = `gap_percent x importance_weight`
4. Classifies severity using either:
   - **ML model** (Gradient Boosted classifier) — if available
   - **Deterministic thresholds** — <=20% = LOW, <=50% = MEDIUM, >50% = HIGH
5. Generates a human-readable **explanation** for each gap
6. Persists results to the `skill_gaps` table

**Key Feature:** The engine uses **skill normalization** — if a student has "React.js" but the role requires "React", the equivalence engine recognizes them as the same skill and gives proper credit.

---

### 7.2 Recommendation Engine (`services/recommender.py`)

A **6-factor hybrid recommendation engine** that ranks courses from the catalog.

**Scoring Factors:**

| Factor | Weight | Description |
|---|---|---|
| Skill Gap Relevance | 0.35 | How directly does this course address the student's identified gaps? |
| Learning Level Fit | 0.20 | Does the course difficulty match the student's current level? (Beginner courses for proficiency <35%, etc.) |
| Content Similarity | 0.15 | TF-IDF cosine similarity between course description and gap skill keywords |
| Quality | 0.10 | Course rating (0-5 scale) |
| User Preference | 0.10 | Prior enrollment/completion signals |
| Diversity | 0.10 | Penalizes recommending too many courses for the same skill |

**Final Score:**
```
score = sum(weight_i x factor_i)
```

Weights are **configurable** per request and auto-normalized to sum to 1.0. Each recommendation run is snapshotted in `RecommendationRun` for reproducibility.

---

### 7.3 Resume Intelligence (`services/resume_parser.py` + `resume_service.py`)

A multi-stage NLP pipeline that extracts structured data from PDF/DOCX resumes.

**Pipeline:**
```
Upload → Text Extraction (pypdf/python-docx)
       → Text Normalization (lowercase, collapse whitespace)
       → Section Detection (skills, experience, projects, education, certifications)
       → Candidate Skill Matching (against 350+ canonical skill patterns)
       → Confidence Scoring (section-based: skills section = 0.95, experience = 0.80)
       → Canonical Skill Mapping (via skill_normalizer)
       → Evidence Record Creation (SkillEvidence rows)
       → StudentSkill Update
       → AI Extraction Audit Record
```

**What Gets Extracted:**
- Programming languages (Python, Java, C++, etc.)
- Frameworks (React, Django, Spring Boot, etc.)
- Databases (PostgreSQL, MongoDB, etc.)
- Cloud platforms (AWS, GCP, Azure)
- DevOps tools (Docker, Kubernetes, Jenkins)
- Projects (title, description, skills used)
- Certifications (name, issuer)

**Unknown Skills:** Terms that can't be mapped to the canonical catalog are sent to the `unknown_skill_reviews` table for human review instead of silently polluting the skill catalog.

---

### 7.4 Skill Normalizer (`services/skill_normalizer.py`)

A canonicalization engine with **350+ alias mappings** that ensures consistent skill identification across the entire system.

**Examples:**
```
"Postgres"  → "PostgreSQL"
"React.js"  → "React"
"ML"        → "Machine Learning"
"k8s"       → "Kubernetes"
"ES6"       → "JavaScript"
"CSS"       → "CSS3"
"py"        → "Python"
```

**Two Key Functions:**

1. **`canonicalize_skill_name(raw)`** — Maps any raw skill text to its canonical form using the alias dictionary
2. **`get_equivalent_skill_ids(skill_id)`** — Returns all database skill IDs that belong to the same equivalence family (so "CSS" and "CSS3" records both count toward the same requirement)

This prevents issues like: a student enters "React.js" but the role requires "React" — without normalization, the system would wrongly report a 100% gap.

---

### 7.5 Role Matcher (`services/role_matcher.py`)

Computes **role readiness scores** with evidence-based confidence.

**Algorithm:**
```
readiness_score = sum(min(user_level, required_level) x weight)
                / sum(required_level x weight) x 100
```

**Confidence Scoring by Evidence Type:**

| Evidence Type | Confidence Weight |
|---|---|
| Assessment / Certification | 1.0 (fully verified) |
| Resume-extracted | 0.6 |
| Self-reported | 0.3 |
| Unacquired | 0.0 |

**Output per role:** match score, core skill coverage %, missing skills, weak skills, strong skills, confidence rating, and verdict (Strong Match / Competitive / Developing / Needs Work).

---

### 7.6 Learning Path Generator (`services/learning_path.py`)

Creates a **phased, ordered study roadmap** for a student targeting a specific role.

**Phases:**

| Phase | Severity | Description |
|---|---|---|
| Phase 1 — Critical | HIGH | Fill the most critical skill gaps first |
| Phase 2 — Core Development | MEDIUM | Build up moderate gaps |
| Phase 3 — Final Polish | LOW | Fine-tune remaining minor gaps |

**Estimated Study Hours by Difficulty:**

| Difficulty | Hours |
|---|---|
| Beginner | 20 |
| Intermediate | 35 |
| Advanced | 50 |
| Unknown | 25 |

The generator uses alias-aware course lookups, so courses tagged with "CSS" can satisfy a "CSS3" skill gap.

---

### 7.7 Analytics Service (`services/analytics.py`)

Computes skill progress analytics from the `Reassessment` history:

- **Skill growth timeline** — per-skill proficiency over time
- **Top improved skills** — which skills showed the most gain
- **Regressed skills** — any skills that declined
- **Improvement velocity** — average gain per reassessment event
- **Assessment performance** — pass rates and score trends
- **Gap reduction** — before/after comparison across roles
- **Role readiness trend** — how match scores evolve over time

---

## 8. API Layer

The API is organized into two layers:

### 8.1 Legacy API (`/api/`)

The original `routes.py` file (26KB) containing all endpoints in a single file. Still functional but being migrated to v1 blueprints.

### 8.2 v1 API Blueprints (`/api/v1/`)

Modular, clean API with standardized response envelope:

```json
{
  "success": true,
  "data": { ... },
  "meta": { ... }
}
```

**Error Response:**
```json
{
  "success": false,
  "message": "Skill not found"
}
```

### Complete API Reference

#### Authentication (`/api/auth/`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Create account (name, email, password) → returns JWT |
| `POST` | `/api/auth/login` | Authenticate → returns access + refresh tokens |
| `GET` | `/api/auth/me` | Get current user profile (requires JWT) |
| `POST` | `/api/auth/refresh` | Exchange refresh token for new access token |

#### Students (`/api/v1/students/`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/students` | List all students |
| `POST` | `/api/v1/students` | Create a new student profile |
| `GET` | `/api/v1/students/<id>` | Get student details |
| `PUT` | `/api/v1/students/<id>` | Update student profile |
| `GET` | `/api/v1/students/<id>/skills` | List student's skills |
| `POST` | `/api/v1/students/<id>/skills` | Add skills to student |

#### Skills (`/api/v1/skills/`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/skills` | List all canonical skills (filterable by category) |

#### Roles (`/api/v1/roles/`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/roles` | List all job roles with skill requirements |

#### Assessments (`/api/v1/assessments/`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/students/<id>/assessments` | Submit assessment score for a skill |

#### Resumes (`/api/v1/resumes/`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/students/<id>/resume` | Upload resume (PDF/DOCX) → triggers NLP extraction |
| `GET` | `/api/v1/students/<id>/evidence` | View extracted skill evidence with confidence |

#### Gap Analysis (`/api/v1/gap-analysis/`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/students/<id>/gap-analysis` | Run skill gap analysis against a target role |
| `GET` | `/api/v1/students/<id>/gap-analysis` | Get latest gap results |

#### Recommendations (`/api/v1/recommendations/`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/students/<id>/recommendations` | Generate course recommendations |
| `GET` | `/api/v1/students/<id>/recommendations` | Get latest recommendations |

#### Learning (`/api/v1/learning/`)

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/students/<id>/learning-path` | Generate phased learning roadmap |
| `GET` | `/api/v1/students/<id>/learning-path` | Get current learning path |
| `PUT` | `/api/v1/students/<id>/learning-progress/<pid>` | Update course completion status |
| `POST` | `/api/v1/students/<id>/reassess` | Reassess a skill after learning |

#### Analytics (`/api/v1/analytics/`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/students/<id>/analytics` | Full skill growth analytics report |

#### Frontend Pages

| URL | Description |
|---|---|
| `GET /` | Home page — student setup, auth, role selection, match scores |
| `GET /skills` | Skills management, resume parser, job role skills, gap analysis |
| `GET /learning` | Learning path, recommendations, progress tracking, analytics |

---

## 9. Machine Learning Pipeline

### 9.1 Training Data Generation (`ml/generate_dataset.py`)

Generates synthetic training data with features derived from the domain model:

| Feature | Type | Description |
|---|---|---|
| `gap_percent` | Numeric | Primary signal — direct gap percentage |
| `assessment_score` | Numeric | Latest assessment score for the skill |
| `current_proficiency` | Numeric | Student's current level (0-100) |
| `required_proficiency` | Numeric | Role's required level (0-100) |
| `project_count` | Numeric | Number of projects using this skill |
| `certification_count` | Numeric | Number of relevant certifications |
| `role_importance` | Numeric | How important this skill is for the role (0-1) |
| `skill_category` | Categorical | Skill category (Programming, Database, etc.) |
| **`gap_level`** | **Target** | **LOW / MEDIUM / HIGH** |

### 9.2 Model Training (`ml/train.py`)

Trains and evaluates **4 models**, selects the best by weighted F1 score:

| Model | Type | Purpose |
|---|---|---|
| Logistic Regression | Linear | Interpretable baseline |
| Decision Tree | Tree | Simple non-linear |
| Random Forest | Ensemble | Variance reduction |
| **Gradient Boosting** | **Ensemble** | **Often best on tabular data (typically selected)** |

**Training Pipeline:**
```
Raw Features → Imputation (median for numeric, mode for categorical)
             → Scaling (StandardScaler for numeric)
             → Encoding (OneHotEncoder for categorical)
             → Classifier
```

**Evaluation:**
- Accuracy, Precision, Recall, F1 (macro & weighted)
- Confusion Matrix
- 5-fold Stratified Cross-Validation
- Best model saved as `ml/models/skill_gap_model.joblib`
- Metrics report saved as `ml/models/metrics_report.json`

### 9.3 ML Inference (at Runtime)

The gap engine **lazily loads** the trained model at first request. If the model file doesn't exist, it falls back to deterministic thresholds — the system never fails due to a missing model.

```python
# In gap_engine.py
severity = ml_model.predict(features)   # ML prediction
# Fallback:
severity = "HIGH" if gap_pct > 50 else "MEDIUM" if gap_pct > 20 else "LOW"
```

---

## 10. Data Sources & Ingestion

### 10.1 ESCO (European Skills, Competences, Qualifications, and Occupations)

- **Version:** v1.2.1
- **Source:** European Commission
- **Scale:** 3,000+ occupations, 13,800+ skills
- **Key Files:**
  - `occupations_en.csv` — Standardized European occupations
  - `skills_en.csv` — Skill/competence definitions
  - `occupationSkillRelations_en.csv` — Essential/optional skill-occupation links
- **Ingested To:** `job_roles`, `skills`, `job_skills` tables
- **CLI:** `flask ingest-data`

### 10.2 O*NET (Occupational Information Network)

- **Version:** v27+
- **Source:** U.S. Department of Labor
- **Key Files:**
  - `Knowledge.xlsx` — Knowledge domains with Importance (IM, 1-5) and Level (LV, 0-7) scales
  - `Work_Activities.xlsx` — Generalized Work Activities
  - `Occupation_Data.xlsx` — SOC occupation codes and descriptions
- **Normalization:** Level values are converted to 0-100 scale (`proficiency = level x 20`)
- **CLI:** `flask ingest-onet`

### 10.3 Coursera Course Catalog

- **Scale:** 3,522 courses
- **Fields:** Course Name, University, Difficulty Level, Rating, URL, Description, Skills
- **Role:** Powers the recommendation engine
- **CLI:** `flask ingest-data` (Coursera portion)

### 10.4 Curated IT Roles & Skills

- **15 IT Job Roles** with exactly **15 core skills each**, manually curated
- **CLI:** `flask sync-roles`
- **Roles Include:** Frontend Developer, Backend Developer, Full Stack Developer, Data Scientist, ML Engineer, DevOps Engineer, Cloud Architect, Cybersecurity Analyst, Mobile App Developer, Database Administrator, QA Engineer, UI/UX Designer, Data Engineer, AI Research Engineer, System Administrator

### 10.5 Curated Courses

- Role-specific learning resources seeded via `seed_courses.py` (91KB of curated data)
- **CLI:** `flask seed-courses`

### 10.6 Student Test Data

- ~20 realistic student profiles with Indian names, degrees, and self-reported skills
- Used for development and testing
- **CLI:** `flask ingest-data` (student portion)

### 10.7 Import Tracking

Every CLI import command records to the `import_batches` table:
- Source identifier
- Start/end timestamps
- Status (running / success / failed)
- Row counts (inserted, updated, skipped)
- Error summary (if failed)

---

## 11. Authentication & Security

### 11.1 JWT Authentication

- **Token Type:** JWT Bearer tokens (access + refresh)
- **Access Token TTL:** 7 days
- **Refresh Token TTL:** 30 days
- **Identity:** User ID stored as `sub` claim
- **Library:** Flask-JWT-Extended

### 11.2 Password Security

- **Hashing:** bcrypt with auto-generated salt
- **Minimum Length:** 6 characters
- **Storage:** Only bcrypt hash stored, never plaintext

### 11.3 Ownership Guard (`require_student_auth`)

A reusable function that:
1. Verifies the JWT token
2. Extracts the authenticated user's ID
3. Confirms the user's `student_id` matches the URL's `<sid>` parameter
4. Returns 403 if a user tries to access another student's data

### 11.4 Centralized Error Handling

All HTTP error codes (400, 401, 403, 404, 500) return JSON responses — no raw exception messages leak to clients.

### 11.5 CORS

Configured to allow only specified origins (defaults to `localhost:5000` and `127.0.0.1:5000`). Overridable via `CORS_ORIGINS` environment variable.

---

## 12. Caching Strategy

The system uses **4 independent in-memory TTL caches** (via `cachetools`) to avoid redundant computation:

| Cache | Key | TTL | Max Size | Purpose |
|---|---|---|---|---|
| `gap_cache` | `(student_id, role_id)` | 5 min | 1,000 | Cached gap analysis results |
| `rec_cache` | `student_id` | 10 min | 500 | Cached recommendations |
| `match_cache` | `student_id` | 5 min | 500 | Cached role match scores |
| `path_cache` | `(student_id, role_id)` | 10 min | 500 | Cached learning paths |

**Invalidation:** Calling `invalidate_student(student_id)` clears all cached data for that student when their skills, assessments, or profile change.

**Thread Safety:** All cache operations are protected by a `threading.RLock`.

---

## 13. Frontend (Templates)

The system includes **3 Jinja2 HTML pages** served directly by Flask:

### 13.1 Home Page (`index.html`) — 24KB
- User registration and login
- Student profile setup (name, email, course, year, target career)
- Job role selection
- Role match score display with visual gauges

### 13.2 Skills Page (`skills.html`) — 32KB
- Manual skill entry with proficiency ratings
- Resume upload (PDF/DOCX) with drag-and-drop
- Extracted skills review with confidence indicators
- Job role skill requirements browser
- Gap analysis visualization (severity color-coded)

### 13.3 Learning Page (`learning.html`) — 35KB
- Phased learning roadmap (Critical → Core → Polish)
- Course recommendations with scores
- Progress tracking (started / in progress / completed)
- Skill reassessment after course completion
- Analytics dashboard (skill growth charts, improvement trends)

---

## 14. Testing

### Test Suite Structure

| Test File | Tests | Coverage |
|---|---|---|
| `test_api.py` | Legacy API endpoints | CRUD, error handling |
| `test_v1_api.py` | v1 API blueprints | All v1 endpoints |
| `test_gap_engine.py` | Gap engine logic | Gap computation, ML fallback, severity |
| `test_recommender.py` | Recommendation engine | Scoring, weights, diversity |
| `test_resume_parser.py` | Resume parsing | PDF/DOCX extraction, skill matching |
| `test_skill_normalizer.py` | Skill normalization | Alias mapping, equivalence families |
| `test_onet_ingest.py` | O*NET data ingestion | Import logic, normalization |

### Test Infrastructure

- **Framework:** pytest with pytest-flask
- **Database:** In-memory SQLite (auto-created per test session via `conftest.py`)
- **Fixtures:** App factory, test client, pre-populated roles/skills/students
- **Expected Pass Count:** 126+ tests

### Running Tests

```bash
cd AI_Skill_Gap_Backend_Implementation
source .venv/bin/activate
python -m pytest              # Run all tests
python -m pytest -v           # Verbose output
python -m pytest tests/test_v1_api.py -v    # Specific file
```

---

## 15. Setup & Deployment

### Quick Start (Linux/Mac)

```bash
# 1. Clone
git clone https://github.com/Raghavendra0348/Backend.git
cd Backend/AI_Skill_Gap_Backend_Implementation

# 2. Virtual environment
python -m venv .venv
source .venv/bin/activate

# 3. Dependencies
pip install -r requirements.txt

# 4. Environment config
cp .env.example .env
# Edit .env with your DATABASE_URL, SECRET_KEY, etc.

# 5. Database setup
flask db upgrade

# 6. Seed data
flask sync-roles      # 15 IT roles + core skills
flask seed-courses    # Curated learning resources
flask ingest-data     # ESCO, Coursera, students
flask ingest-onet     # O*NET knowledge + activities

# 7. (Optional) Train ML model
flask train-model

# 8. Run
flask --app app run --debug
```

Server starts at: **http://127.0.0.1:5000**

### CLI Commands Reference

| Command | Description |
|---|---|
| `flask init-db` | Create all database tables |
| `flask db upgrade` | Apply Alembic migrations |
| `flask sync-roles` | Sync 15 IT roles with 15 skills each |
| `flask seed-courses` | Seed curated courses for role skills |
| `flask ingest-data` | Ingest ESCO + Coursera + student data |
| `flask ingest-onet` | Ingest O*NET knowledge + activities |
| `flask train-model` | Generate dataset + train ML model |

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | `dev-secret-...` | Flask secret key |
| `JWT_SECRET_KEY` | `jwt-dev-secret-...` | JWT signing key |
| `DATABASE_URL` | `sqlite:///skill_gap.db` | Database connection string |
| `UPLOAD_DIR` | `storage/uploads` | Resume upload directory |
| `MODEL_PATH` | `ml/models/skill_gap_model.joblib` | Trained ML model path |
| `MAX_CONTENT_LENGTH` | `5242880` (5MB) | Max upload file size |
| `CORS_ORIGINS` | `localhost:5000,...` | Allowed CORS origins |
| `ESCO_DATA_DIR` | Auto-detected | ESCO CSV directory |
| `ONET_KNOWLEDGE_XLSX` | Auto-detected | O*NET Knowledge file |
| `ONET_ACTIVITIES_XLSX` | Auto-detected | O*NET Activities file |
| `ONET_OCCUPATIONS_XLSX` | Auto-detected | O*NET Occupations file |
| `COURSERA_CSV` | Auto-detected | Coursera catalog file |
| `STUDENT_DATASET_XLSX` | Auto-detected | Student profiles file |

---

## 16. Data Flow Walkthrough

### Scenario: A student signs up, uploads a resume, and gets a learning path

```
1. REGISTER
   POST /api/auth/register {name, email, password}
   → Creates User + Student records
   → Returns JWT access token

2. SET TARGET CAREER
   PUT /api/v1/students/<id> {target_career: "Full Stack Developer"}

3. UPLOAD RESUME
   POST /api/v1/students/<id>/resume  [resume.pdf]
   → pypdf extracts text
   → NLP pipeline detects sections (skills, experience, projects)
   → Pattern matcher finds "React", "Node.js", "PostgreSQL", etc.
   → skill_normalizer maps "Postgres" → "PostgreSQL", "React.js" → "React"
   → Unknown terms → unknown_skill_reviews queue
   → Creates SkillEvidence rows (with confidence + evidence_span)
   → Creates/updates StudentSkill rows (proficiency estimated from context)
   → Logs AIExtractionRecord (latency, counts)

4. GAP ANALYSIS
   POST /api/v1/students/<id>/gap-analysis {job_role_id: 3}
   → Fetches student skills vs Full Stack Developer requirements
   → For each required skill:
       gap = max(0, 70 - 45) = 25
       gap_pct = 25/70 x 100 = 35.7%
       severity = ML_model.predict(features) → "MEDIUM"
       priority = 35.7 x 0.9 (importance) = 32.1
   → Generates explanation: "PostgreSQL: Currently at 45/100, role requires 70/100.
      Gap of 35.7%. Evidence: resume-extracted (confidence: 0.80)"
   → Persists SkillGap rows
   → Caches result for 5 min

5. RECOMMENDATIONS
   POST /api/v1/students/<id>/recommendations
   → Retrieves gap analysis results
   → For each gap skill, queries Course + CourseSkill catalog
   → Scores each candidate course with 6 factors:
       0.35 x skill_gap_relevance
       0.20 x learning_level_fit (Intermediate matches 45% proficiency)
       0.15 x TF-IDF cosine similarity
       0.10 x course_rating/5.0
       0.10 x user_preference_signal
       0.10 x diversity_penalty
   → Ranks, deduplicates, limits to top-N per skill
   → Saves RecommendationRun snapshot (JSON)
   → Returns sorted recommendations with reasons

6. LEARNING PATH
   POST /api/v1/students/<id>/learning-path {job_role_id: 3}
   → Phase 1 (Critical): HIGH severity gaps first
       Step 1: "Advanced Docker & Kubernetes" (50 hrs) — for Docker gap
       Step 2: "CI/CD with Jenkins" (35 hrs) — for DevOps gap
   → Phase 2 (Core): MEDIUM severity gaps
       Step 3: "PostgreSQL Masterclass" (35 hrs) — for PostgreSQL gap
   → Phase 3 (Polish): LOW severity gaps
       Step 4: "Git Advanced Workflows" (20 hrs) — for Git gap
   → Total: 4 courses, 140 estimated hours
   → Persists LearningPath + LearningPathStep rows

7. PROGRESS TRACKING
   PUT /api/v1/students/<id>/learning-progress/<pid> {completion: 75, status: "in_progress"}
   → Updates LearningProgress record

8. REASSESSMENT
   POST /api/v1/students/<id>/reassess {skill_id: 12, new_level: 68}
   → Records Reassessment (old_level=45, new_level=68, improvement=+23)
   → Updates StudentSkill proficiency
   → Invalidates caches
   → Next gap analysis will show reduced gap

9. ANALYTICS
   GET /api/v1/students/<id>/analytics
   → Returns: skill_timeline, top_improved, improvement_velocity,
     assessment_performance, gap_reduction_trend
```

---

## 17. Key Algorithms & Formulas

### Gap Computation (Deterministic Baseline)

```
gap       = max(0, required_level - current_level)
gap_pct   = (gap / required_level) x 100        [0-100%]
priority  = gap_pct x importance_weight           [0-100]
```

### Severity Classification

```
if gap_pct <= 20%   → LOW
if gap_pct <= 50%   → MEDIUM
if gap_pct >  50%   → HIGH
```

### Role Readiness Score

```
readiness = sum(min(user_level, required_level) x importance)
          / sum(required_level x importance)
          x 100
```

### Recommendation Score (6-Factor)

```
score = 0.35 x skill_gap_relevance
      + 0.20 x learning_level_fit
      + 0.15 x content_similarity      (TF-IDF cosine)
      + 0.10 x quality                 (rating / 5.0)
      + 0.10 x user_preference
      + 0.10 x diversity
```

### Evidence Confidence Weights

```
Assessment/Certification  → 1.00  (fully verified)
Resume-extracted          → 0.75 - 0.95  (section-dependent)
Self-reported             → 0.30
Unacquired                → 0.00
```

### Learning Level Fit

```
Beginner course     → optimal when proficiency < 35%
Intermediate course → optimal when 30% < proficiency < 75%
Advanced course     → optimal when proficiency > 65%
```

---

## 18. Future Development Roadmap

The project has an 11-stage development roadmap (see `staged_development_plan.md`):

| Stage | Name | Status | Priority |
|---|---|---|---|
| 0 | Audit & Freeze | Done | — |
| 1 | Security & Identity | Planned | CRITICAL |
| 2 | Database & Taxonomy Cleanup | Planned | CRITICAL |
| 3 | Route & Service Architecture | Planned | HIGH |
| 4 | Skill Assessment System | Planned | HIGH |
| 5 | Core Skill Intelligence | Planned | HIGH |
| 6 | AI Resume Intelligence | Planned | HIGH |
| 7 | Recommendation Intelligence | Mostly Done | HIGH |
| 8 | Learning Intelligence | Planned | HIGH |
| 9 | Data Platform | Planned | MEDIUM |
| 10 | Production Infrastructure | Planned | MEDIUM |
| 11 | Analytics | Planned | MEDIUM |

### Key Planned Improvements

- **Enforce JWT on all student-private routes** — derive student_id from token, not URL
- **Separate `users` from `students`** — clean auth/profile separation
- **Add `skill_aliases` and `skill_categories` tables** — stop silently creating canonical skills
- **Prerequisite-aware learning paths** — dependency graphs (JS → TS → React)
- **Redis cache** — replace in-memory TTLCache for multi-worker deployments
- **Background workers** (Celery/RQ) — for long-running resume processing and data imports
- **Structured audit logging** — request IDs and response latency tracking
- **Health endpoints** — `/api/v1/health/live` and `/api/v1/health/ready`

---

*This document provides a complete technical explanation of the AI Skill Gap Prediction & Learning Recommendation System backend. For setup instructions, see `WINDOWS_SETUP_GUIDE.md`. For the detailed improvement plan, see `staged_development_plan.md`.*
