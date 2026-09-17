# AI-Based Skill Gap Prediction & Learning Recommendation System

**Project Code:** MCA\_MP\_69  
**Institution:** Presidency University — MCA Final Year Project  
**Role:** Backend & ML Model Developer  

---

## Overview

A full-stack backend system that analyses a student's skill profile against industry job roles and predicts **skill gaps** using a trained ML classifier. It then recommends personalised Coursera courses and generates a structured **learning roadmap** to close those gaps.

The system uses two internationally recognised competency taxonomies:

- **ESCO v1.2.1** — European skills/competences/qualifications/occupations (7,691 records ingested)
- **O\*NET 27.0** — U.S. Occupational Information Network (knowledge, work activities, occupations)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | Flask 3.x (Python 3.12) |
| Database | MySQL (production) / SQLite (local dev) |
| ORM | Flask-SQLAlchemy |
| ML | scikit-learn — Decision Tree Classifier |
| Auth | Flask-JWT-Extended + bcrypt |
| Caching | cachetools TTLCache (in-memory, thread-safe) |
| NLP / Resume | spaCy, NLTK, pypdf, python-docx |
| Data | pandas, numpy, openpyxl |
| Testing | pytest, pytest-flask |

---

## Project Structure

```
AI_Skill_Gap_Backend_Implementation/
│
├── app.py                  # Flask app factory — registers blueprints, CLI commands
├── config.py               # Config class (DB, JWT, paths)
├── extensions.py           # Shared db = SQLAlchemy() instance
├── models.py               # SQLAlchemy ORM models (all 15 tables)
├── routes.py               # Main REST API blueprint (~875 lines, 25+ endpoints)
├── auth.py                 # JWT auth blueprint (register / login / me / refresh)
├── cache.py                # Thread-safe TTL cache for gap, rec, match, path results
├── seed.py                 # Demo seed (6 job roles, 48 skills, 25 courses, 1 student)
│
├── services/
│   ├── gap_engine.py       # ML gap analysis — loads model, runs inference
│   ├── recommender.py      # Course recommendation engine (skill-gap weighted scoring)
│   ├── resume_parser.py    # PDF/DOCX resume parser (spaCy + NLTK)
│   ├── role_matcher.py     # Weighted job role match score calculator
│   ├── learning_path.py    # Phased learning roadmap generator (HIGH/MEDIUM/LOW)
│   └── analytics.py        # Skill progress analytics, trend & regression detection
│
├── ml/
│   ├── generate_dataset.py # Synthetic dataset generator (5,000 rows)
│   ├── train.py            # Trains 4 models, picks best by F1, saves .joblib
│   ├── skill_gap_dataset.csv   # Generated training dataset (5,000 rows) [gitignored]
│   └── models/
│       ├── skill_gap_model.joblib   # Best trained model: Decision Tree (F1=0.9990) [gitignored]
│       └── metrics_report.json      # All model comparison results
│
├── data/
│   ├── ingest.py           # ESCO + O*NET + Coursera + Student CSV ingestion pipeline
│   ├── external/           # Place raw ESCO/O*NET CSV files here (not committed)
│   └── __init__.py
│
├── templates/
│   ├── index.html          # Page 1: Home — Auth, student/role setup, match scores
│   ├── skills.html         # Page 2: Skills, Resume Parser, Job Role skills, ML Gap Analysis
│   └── learning.html       # Page 3: Learning Path, Recommendations, Progress, Analytics
│
├── tests/
│   ├── conftest.py         # pytest fixtures (test app, seeded client)
│   ├── test_api.py         # API endpoint integration tests
│   ├── test_gap_engine.py  # ML gap engine unit tests
│   ├── test_gap.py         # Gap analysis API tests
│   ├── test_onet_ingest.py # O*NET ingestion tests
│   ├── test_recommender.py # Recommendation engine tests
│   └── test_resume_parser.py  # Resume parser tests
│
├── storage/uploads/        # User-uploaded resume files [gitignored]
├── instance/               # SQLite dev database [gitignored]
├── .env                    # Local environment variables (DB URL, secrets) [gitignored]
├── .env.example            # Template for setting up .env
├── .gitignore
├── pytest.ini
├── requirements.txt
└── PROJECT_COMPLETION_STATUS.md

Dataset/ (Parent Dataset Repository — Clean & Structured)
├── README.md               # Dataset catalog and schemas
├── onet/                   # O*NET Knowledge, Occupation Data & Work Activities (XLSX)
├── coursera/               # Coursera course catalogue (Coursera.csv & Coursera.zip)
├── students/               # Student profiles (Indian Names) & academic risk datasets
└── esco/                   # Official ESCO v1.2.1 classification CSVs & archive
```

---

## Database Models (15 Tables)

| Model | Description |
|---|---|
| `Student` | Student profile (name, email, course, graduation year, target career) |
| `Skill` | Canonical skill catalogue (from ESCO + O\*NET) |
| `StudentSkill` | Student's proficiency per skill with evidence type |
| `JobRole` | Job roles from ESCO/O\*NET with SOC codes |
| `JobSkill` | Required skills per role with importance weights |
| `Course` | Coursera courses linked to skills |
| `CourseSkill` | Skills taught by each course |
| `Assessment` | Skill assessment scores (auto-calculates proficiency) |
| `SkillGap` | Persisted ML gap predictions (HIGH/MEDIUM/LOW) |
| `Recommendation` | Course recommendations per student skill gap |
| `LearningProgress` | Course completion tracking |
| `Project` | Student projects (evidence of skills) |
| `Certification` | Student certifications |
| `Reassessment` | Post-learning reassessment results with improvement delta |
| `Resume` | Uploaded resume metadata |
| `User` | Auth accounts (JWT) linked to Student profiles |
| `LearningPath` | Generated phased learning roadmaps |
| `LearningPathStep` | Individual course steps within a learning path |

---

## API Endpoints

### Auth — `/api/auth`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Create account + student profile, returns JWT |
| POST | `/api/auth/login` | Login, returns access + refresh tokens |
| GET | `/api/auth/me` | Get current user profile (requires token) |
| POST | `/api/auth/refresh` | Refresh access token |

### Students — `/api/students`

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/students` | Create student profile |
| GET | `/api/students` | List all students |
| GET | `/api/students/<id>` | Get student profile + skills |
| PUT | `/api/students/<id>` | Update target career / graduation year |
| POST | `/api/students/<id>/skills` | Add or update a skill proficiency |
| POST | `/api/students/<id>/assessments` | Submit assessment score (auto-calculates proficiency) |
| POST | `/api/students/<id>/projects` | Add project |
| POST | `/api/students/<id>/certifications` | Add certification |
| POST | `/api/students/<id>/resume` | Upload PDF/DOCX resume, extract skills |
| POST | `/api/students/<id>/progress` | Log course progress |
| POST | `/api/students/<id>/reassessment` | Submit post-learning reassessment |
| GET | `/api/students/<id>/gaps` | Retrieve persisted skill gaps |
| GET | `/api/students/<id>/recommendations` | Get top-K course recommendations |
| GET | `/api/students/<id>/dashboard` | Full dashboard summary |
| GET | `/api/students/<id>/role-match` | Job role match scores (all roles or specific) |
| POST | `/api/students/<id>/learning-path` | Generate phased learning roadmap |
| GET | `/api/students/<id>/learning-path` | Retrieve saved learning path |
| GET | `/api/students/<id>/analytics` | Skill progress analytics + trends |

### Roles & Analysis

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/roles` | List all job roles |
| GET | `/api/roles/<id>/skills` | Required skills for a role |
| POST | `/api/skill-gap/analyze` | Run ML gap analysis (student vs role) |

### Utility

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Backend health check |
| GET | `/api/cache/stats` | In-memory cache statistics |

---

## ML Model

### Task
Multi-class classification: predict skill gap severity as **HIGH**, **MEDIUM**, or **LOW**.

### Features (8)

| Feature | Description |
|---|---|
| `gap_percent` | `(required - current) / required * 100` — primary signal |
| `assessment_score` | Verified test score (0–100) |
| `current_proficiency` | Student's current skill level |
| `required_proficiency` | Role's required level |
| `project_count` | Number of projects using this skill |
| `certification_count` | Relevant certifications held |
| `role_importance` | Skill importance weight for the role |
| `skill_category` | Encoded skill domain (Programming, Data, etc.) |

### Model Comparison

| Model | Accuracy | F1 (weighted) | CV F1 Mean |
|---|---|---|---|
| **Decision Tree** | **0.9990** | **0.9990** | **0.9992** |
| Gradient Boosting | 0.9990 | 0.9990 | 0.9992 |
| Random Forest | 0.9980 | 0.9980 | 0.9995 |
| Logistic Regression | 0.9880 | 0.9880 | 0.9792 |

Best model: **Decision Tree** (selected for lowest latency at equal F1).  
Training: 4,000 rows | Test: 1,000 rows | Dataset: 5,000 synthetic rows.

---

## Setup & Running

### Prerequisites
- Python 3.12+
- MySQL 8.0+ (or use SQLite for local dev — no config needed)

### 1. Clone & Install

```bash
cd AI_Skill_Gap_Backend_Implementation
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env — set DATABASE_URL for MySQL (leave blank to use SQLite)
```

```env
DATABASE_URL=mysql+pymysql://user:password@localhost/skill_gap_db
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret-key
```

### 3. Initialise Database & Seed

```bash
flask --app app init-db        # Create all tables
flask --app app seed           # Load demo data (6 roles, 48 skills, 25 courses)
```

### 4. Ingest Real Data (ESCO + O*NET + Coursera)

```bash
flask --app app ingest-data    # Loads 7,691 ESCO/O*NET/Coursera records
flask --app app ingest-onet    # Load O*NET knowledge & work activities
```

### 5. Train the ML Model

```bash
python ml/generate_dataset.py --output ml/skill_gap_dataset.csv --rows 5000
python ml/train.py --input ml/skill_gap_dataset.csv --output ml/models/skill_gap_model.joblib
```

### 6. Run Tests

```bash
pytest tests/ -v
# Expected: 84 passed, 6 skipped
```

### 7. Start the Server

```bash
flask --app app run --debug --port 5000
```

Open **http://localhost:5000** for the interactive UI.

---

## UI Pages

| URL | Page | Features |
|---|---|---|
| `/` | Home & Setup | Auth (login/register), student & role selection, job role match scores |
| `/skills` | Skills & Gap Analysis | Add skills, resume parser, role skill explorer, ML gap analysis |
| `/learning` | Learning & Analytics | Phased learning path, recommendations, progress log, reassessment, skill analytics |

State (student ID, role ID, JWT token) is shared across pages via `sessionStorage`.

---

## Caching

Responses are cached in-memory using `cachetools.TTLCache` with thread-safe `RLock`:

| Cache | TTL | Contents |
|---|---|---|
| `gap_cache` | 10 min | Gap analysis results per student+role |
| `rec_cache` | 10 min | Course recommendations per student+role |
| `match_cache` | 5 min | Role match scores per student |
| `path_cache` | 30 min | Generated learning paths per student+role |

Cache is automatically invalidated when skill data is updated.  
Inspect at `GET /api/cache/stats`.

---

## Running Tests

```bash
pytest tests/ -v                   # All tests with verbose output
pytest tests/test_api.py -v        # API integration tests only
pytest tests/test_gap_engine.py -v # ML engine unit tests only
```

---

## Key Design Decisions

- **Dual taxonomy (ESCO + O\*NET):** ESCO covers technical/professional roles; O\*NET adds cognitive, knowledge, and work activity dimensions — together giving richer gap signals than either alone.
- **SQLAlchemy `create_all()`** is the single schema source of truth — no raw SQL migration files.
- **In-memory caching** (not Redis) to keep deployment simple while still giving significant latency reduction for repeated gap analysis calls.
- **JWT auth** is stateless — tokens are 7-day access / 30-day refresh, stored client-side.
- **ML inference** runs synchronously in the Flask request thread — model is pre-loaded at startup via `joblib`.
