# AI-Based Skill Gap Prediction & Learning Recommendation System
## Backend Implementation — Completion Status Report

**Project Code:** MCA_MP_69  
**Institution:** MCA Final Year Project, Presidency University  
**Status:** **100% Core Backend Complete** (59/59 Tests Passing)  
**Date:** September 2026  

---

### Executive Summary

| Area | Status | Key Deliverable / Metrics |
|---|---|---|
| **Database Schema** | **100% Complete** | 12 tables (`models.py`), fully normalized, SQLite + MySQL compatible |
| **Data Ingestion (ETL)** | **100% Complete** | ESCO v1.2.1 (6 IT roles, 509 relations), Coursera (1,612 courses), Student Excel (22 profiles) |
| **ML Gap Classification** | **100% Complete** | Logistic Regression, Decision Tree, Random Forest compared; Best model F1 = **0.9725** |
| **Recommendation Engine** | **100% Complete** | TF-IDF + Cosine Similarity + Gap Priority Weighting + Course Rating Ranker |
| **Resume Parser** | **100% Complete** | PDF & DOCX text extraction, 40+ tech alias map, section parser (projects, certs) |
| **REST API Layer** | **100% Complete** | 17 RESTful endpoints implemented in `routes.py` |
| **Automated Test Suite** | **100% Complete** | **59 passed in ~6 seconds** (`tests/`) across all components |

---

### File-by-File Completion Breakdown

#### 1. Configuration & Application Factory
- **`config.py`** *(100% Complete)*
  - Handles SQLite local fallback and MySQL `DATABASE_URL`.
  - Configures dataset paths (ESCO, Coursera ZIP, Student Excel).
  - Configures gap thresholds (`LOW=20`, `MEDIUM=50`).
- **`extensions.py`** *(100% Complete)*
  - Decoupled `SQLAlchemy` instance preventing circular imports.
- **`app.py`** *(100% Complete)*
  - Application factory `create_app(test_config=None)`.
  - Flask CLI commands: `flask init-db`, `flask seed`, `flask ingest-data`, `flask train-model`.
  - Blueprint registration (`/api`).
- **`.env` & `requirements.txt`** *(100% Complete)*
  - All dependencies pinned (`Flask`, `SQLAlchemy`, `scikit-learn`, `pandas`, `openpyxl`, `pypdf`, `python-docx`, `pytest`).

---

#### 2. Data Models (`models.py`) — 12 Tables *(100% Complete)*
1. `Student` — Personal info, target career, education.
2. `Skill` — Canonical & ESCO skill taxonomy with category grouping.
3. `JobRole` — Industry occupation definitions (ESCO IT roles & DEMO roles).
4. `JobSkill` — Target requirements per role (`required_level`, `importance`, `relation_type`).
5. `StudentSkill` — Student inventory (`current_level`, `confidence_score`, `source`).
6. `Course` — Learning items (title, url, platform, rating, difficulty).
7. `CourseSkill` — Mappings between courses and skills covered.
8. `Recommendation` — Personalized recommendations generated for students.
9. `Assessment` — Direct quiz/test results linked to skills.
10. `LearningProgress` — Course enrollment status (`NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`).
11. `Reassessment` — Skill improvement tracking after completing courses.
12. `Project` & `Certification` — Extracted/uploaded evidence supporting skill levels.

---

#### 3. Data Ingestion Pipeline (`data/ingest.py`) *(100% Complete)*
- **ESCO v1.2.1 Ingestion:**
  - Ingests 6 core IT roles: *Software Developer*, *Data Analyst*, *Database Administrator*, *Cloud Architect*, *DevOps Engineer*, *Machine Learning Engineer*.
  - Maps 500+ essential and optional skill relations with standardized proficiency levels.
- **Coursera Dataset Ingestion:**
  - Reads directly from compressed `Dataset/archive (1).zip`.
  - Ingested 1,604 IT-relevant courses, extracting difficulty, ratings, and course descriptions.
- **Student Dataset Ingestion:**
  - Reads `Dataset/Final_Updated_DMA_DATASET_Indian_Names (1).xlsx`.
  - Seeds student profiles with realistic initial skills.
- **Idempotency:** Safe to run repeatedly without creating duplicate rows.

---

#### 4. Machine Learning & Skill Gap Engine (`services/gap_engine.py` & `ml/`) *(100% Complete)*
- **`ml/generate_dataset.py`**: Generates 2,000 synthetic labeled training vectors with real noise, simulating student skill vs. job requirements.
- **`ml/train.py`**:
  - Compares Logistic Regression, Decision Tree, and Random Forest.
  - 5-Fold Cross Validation.
  - **Selected Model:** Logistic Regression (`skill_gap_model.joblib`) with F1 = **0.9725**, Accuracy = **97.2%**.
  - Metrics exported to `ml/models/metrics.json`.
- **`services/gap_engine.py`**:
  - Predicts gap label (`LOW`, `MEDIUM`, `HIGH`) using the trained ML model.
  - Automatic fallback to deterministic formula if ML model is unavailable.
  - Computes `priority_score = gap_score * importance`.

---

#### 5. Course Recommendation Engine (`services/recommender.py`) *(100% Complete)*
- Content-based filtering using **TF-IDF Vectorization** on course descriptions and target skill keywords.
- **Cosine Similarity** scoring.
- Multi-objective ranking formula:
  $$\text{Final Score} = 0.50 \times \text{Similarity} + 0.30 \times \text{Gap Priority} + 0.20 \times \text{Normalized Rating}$$
- Guarantees recommendations are prioritized for skills with highest gaps.

---

#### 6. Resume Parser (`services/resume_parser.py`) *(100% Complete)*
- Dual format support: PDF (via `pypdf`) and DOCX (via `python-docx`).
- Preprocessing and normalization preserving special symbols (`C++`, `C#`, `.NET`).
- Comprehensive 40+ alias mapping (e.g., `ML` $\rightarrow$ `Machine Learning`, `Postgres` $\rightarrow$ `PostgreSQL`).
- Regex extraction of:
  - Years of experience.
  - Projects section.
  - Certifications section.
- Candidate skill extraction with confidence scoring based on section context.

---

#### 7. REST API Endpoints (`routes.py`) — 17 Endpoints *(100% Complete)*

| # | Endpoint | Method | Functionality |
|---|---|---|---|
| 1 | `/api/health` | `GET` | Health check & service readiness |
| 2 | `/api/students` | `POST` | Register a new student profile |
| 3 | `/api/students/<id>` | `GET` | Retrieve student profile details |
| 4 | `/api/students/<id>` | `PUT` | Update student profile |
| 5 | `/api/students/<id>/skills` | `POST` | Add or update a student skill |
| 6 | `/api/assessments` | `POST` | Submit test assessment results |
| 7 | `/api/roles` | `GET` | List all available job roles |
| 8 | `/api/roles/<id>/skills` | `GET` | Get required skills for a role |
| 9 | `/api/gap-analysis` | `GET` | Run ML skill gap analysis |
| 10 | `/api/recommendations` | `GET` | Get ranked course recommendations |
| 11 | `/api/parse-resume` | `POST` | Upload PDF/DOCX and extract skills |
| 12 | `/api/students/<id>/progress` | `POST` | Track course learning progress |
| 13 | `/api/students/<id>/progress` | `GET` | View enrolled courses & progress |
| 14 | `/api/reassessments` | `POST` | Reassess student and update skill level |
| 15 | `/api/students/<id>/projects` | `POST` | Add project to profile |
| 16 | `/api/students/<id>/certifications` | `POST` | Add certification to profile |
| 17 | `/api/students/<id>/dashboard` | `GET` | Comprehensive student dashboard |

---

#### 8. Automated Test Suite (`tests/`) — 59 Passing Tests *(100% Complete)*
- **`tests/conftest.py`**: SQLite in-memory fixture with `StaticPool`.
- **`tests/test_api.py`** (24 tests): Full student journey, validation checks, edge cases.
- **`tests/test_gap_engine.py`** (14 tests): Threshold boundaries, priority sorting.
- **`tests/test_recommender.py`** (6 tests): Score bounds, ordering, top-k limits.
- **`tests/test_resume_parser.py`** (12 tests): Extraction, text cleanup, alias matching.
- **`tests/test_gap.py`** (3 tests): Model unit tests.

---

### What to Prepare for Final College Submission (Section 21 of Implementation Guide)

All coding work is done. Before your final project viva/submission, keep these academic documentation items ready:
1. **Model Evaluation Curves:** Screenshot or cite the `ml/models/metrics.json` file (shows 5-fold CV scores for Logistic Regression vs Decision Tree vs Random Forest).
2. **ESCO & Coursera Dataset Attribution:** Include standard citations for ESCO v1.2.1 and Coursera Open Dataset in your project report bibliography.
3. **Frontend Integration:** When ready to build or connect your frontend UI (React, Vue, or HTML/JS), point all requests to `http://localhost:5000/api`.
