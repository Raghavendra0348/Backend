# AI Skill Gap Backend — Development Stages

Based on [`AI_Skill_Gap_Backend_Development_Plan.md`](file:///home/a-raghavendra/Desktop/github_repos/ML_Backend/Backend/AI_Skill_Gap_Backend_Development_Plan%20%281%29.md)

---

## Stage 0 — Audit & Freeze *(CRITICAL — 1–2 days)*

**Goal**: Stabilize the current state before making any structural changes.

| Task | Status |
|------|--------|
| Freeze existing API behavior | ✅ Done |
| Write regression tests for current endpoints | ✅ 100 tests passing |
| Document current endpoints | `README.md` exists |
| Capture baseline DB counts (roles, skills, courses) | Can run anytime |

**Already done in this codebase.** Proceed to Stage 1.

---

## Stage 1 — Security & Identity *(CRITICAL)*

**Goal**: No user can access another user's private resources.

### What to do
- [ ] Enforce JWT on all student-private routes (`/api/students/<id>/*`)
- [ ] Derive `student_id` server-side from the authenticated JWT token — do **not** trust `<sid>` in the URL as authorization
- [ ] Add centralized error handler (no raw exceptions to client)
- [ ] Add strict CORS config
- [ ] Add rate limiting (Flask-Limiter)
- [ ] Add request size limits
- [ ] Security headers (`X-Frame-Options`, `X-Content-Type-Options`, etc.)

### Key files
- [`auth.py`](file:///home/a-raghavendra/Desktop/github_repos/ML_Backend/Backend/AI_Skill_Gap_Backend_Implementation/auth.py)
- [`routes.py`](file:///home/a-raghavendra/Desktop/github_repos/ML_Backend/Backend/AI_Skill_Gap_Backend_Implementation/routes.py)
- [`app.py`](file:///home/a-raghavendra/Desktop/github_repos/ML_Backend/Backend/AI_Skill_Gap_Backend_Implementation/app.py)

---

## Stage 2 — Database & Taxonomy Cleanup *(CRITICAL)*

**Goal**: Canonical, deduplicated, normalized data model.

### What to do
- [ ] Separate `users` (auth) from `user_profiles` (student data) — remove the current fragile User↔Student dual-identity
- [ ] Add `skill_aliases` table (stop silently creating canonical skills from arbitrary input)
- [ ] Add `skill_categories` table with hierarchy
- [ ] Add `external_skills` + `external_skill_mappings` tables for ESCO/O*NET — decouple external taxonomies from canonical model
- [ ] Add `role_aliases` table
- [ ] Introduce Flask-Migrate / Alembic for managed migrations
- [ ] Add `import_batches` table to track every data import run

### Current problems to fix
- `_resolve_skill_id()` silently creates new canonical `Skill` rows from arbitrary text → must become an explicit review/unknown workflow
- ESCO and O*NET skills are stored in the same `Skill` table as practical technical skills — needs explicit `source`/`type` separation

---

## Stage 3 — Route & Service Architecture *(HIGH)*

**Goal**: Clean separation between HTTP handling and business logic.

### What to do
- [ ] Split `routes.py` into focused blueprints:
  ```
  api/students.py
  api/skills.py
  api/roles.py
  api/assessments.py
  api/resumes.py
  api/gap_analysis.py
  api/recommendations.py
  api/learning.py
  api/analytics.py
  ```
- [ ] Add service layer: `UserService`, `SkillService`, `RoleService`, `SkillGapService`, `RecommendationService`, `LearningPathService`, `AnalyticsService`
- [ ] No admin service — data management done via CLI commands and seed scripts
- [ ] Version the API: `/api/v1/`
- [ ] Add Marshmallow / Pydantic schema validation for all request inputs
- [ ] Standardize all responses: `{"success": true, "data": {}, "meta": {}}` envelope

---

## Stage 4 — Skill Assessment System *(HIGH)*

**Goal**: Replace the current basic assessment with a proper multi-question system.

### What to do
- [ ] Create DB tables:
  - `assessment_templates`
  - `assessment_questions` + `assessment_question_skills`
  - `assessment_attempts`
  - `assessment_answers`
  - `skill_assessment_results`
- [ ] Score normalization (raw → 0–100)
- [ ] Attempt history per student per skill
- [ ] Assessment feeds into `StudentSkill` confidence/evidence

---

## Stage 5 — Core Skill Intelligence *(HIGH)*

**Goal**: Accurate, explainable skill gap and role readiness.

### What to do
- [ ] Lock deterministic gap formula as source of truth:
  ```
  gap = max(required_level - current_level, 0)
  priority = normalized_gap × importance_weight × evidence_adjustment
  ```
- [ ] Output: `{current, required, gap, gap_pct, severity, priority, evidence_summary, explanation, model_version}`
- [ ] Role readiness score:
  ```
  score = Σ(min(user_level, required_level) × weight) / Σ(required_level × weight) × 100
  ```
- [ ] Separate confidence score for profile verification level (self-reported vs assessed vs verified)
- [ ] Every result must include an explanation (no bare scores)

---

## Stage 6 — AI Resume Intelligence *(HIGH)*

**Goal**: Resume → structured, evidenced skill profile (not just keyword matching).

### Extraction pipeline
```
Resume File → Text Extraction → Section Detection
           → Entity Extraction → Skill Extraction
           → Canonical Mapping → Evidence Spans
           → Confidence Scoring → User Verification
           → Skill Profile Update
```

### What to do
- [ ] Store `skill_evidence` rows per extracted skill (`evidence_type`, `source_id`, `confidence`, `evidence_span`, `section`)
- [ ] All AI-extracted skills must map to canonical catalog before persistence — unknowns go to a **review queue**, not auto-created
- [ ] Layered normalization: exact → alias → fuzzy → embedding → LLM → unknown
- [ ] Add `ai_extraction_records` table (`prompt_version`, `model`, `latency`, `token_usage`, `created_at`)
- [ ] User verification UI flow for AI-extracted skills

---

## Stage 7 — Recommendation Intelligence *(HIGH)*

**Goal**: Personalized, diverse, explainable course ranking.

### Ranking pipeline
```
Candidate Generation → Skill Coverage → Gap Priority
→ Difficulty Fit → Content Similarity → User Preferences
→ Rating/Quality → Diversity → Final Ranking
```

### Scoring weights (configurable)
```
0.35 skill_gap_relevance
0.20 learning_level_fit
0.15 content_similarity
0.10 quality
0.10 user_preference
0.10 diversity
```

### What to do
- [ ] Make scoring weights configurable (not hardcoded)
- [ ] Add `recommendation_runs` / snapshots table (so recommendations are reproducible over time)
- [ ] User preference signals (completed, skipped, enrolled)
- [ ] Difficulty fit (Beginner for proficiency < 30%, Advanced for > 70%)
- [ ] ✅ Smooth TF-IDF cosine (already done)
- [ ] ✅ Role-filtered recommendations (already done)
- [ ] ✅ Diversity-aware ranking (already done)

---

## Stage 8 — Learning Intelligence *(HIGH)*

**Goal**: Dependency-aware learning paths with full progress lifecycle.

### Prerequisite example
```
JavaScript → TypeScript → React → State Management → Testing → Frontend Architecture
```

### What to do
- [ ] Add prerequisite graph to skills (`skill_prerequisites` table)
- [ ] Replace simple `LearningProgress` rows with:
  - `user_learning_enrollments` (one stable record per course per student)
  - `learning_progress_events` (history: started, progress update, completed)
- [ ] Track: `enrolled_at`, `started_at`, `completed_at`, `time_spent`, `completion_pct`
- [ ] Path generation considers: prerequisite graph, current proficiency, gap severity, importance, estimated effort, completed resources
- [ ] Reassessment loop: after completing learning → re-run gap analysis → show updated readiness

---

## Stage 9 — Data Platform *(MEDIUM/HIGH)*

**Goal**: Reliable, idempotent, versioned data imports.

### What to do
- [ ] Split `data/ingest.py` into separate importers:
  ```
  ingestion/esco_importer.py
  ingestion/onet_importer.py
  ingestion/course_importer.py
  ingestion/validator.py
  ingestion/importer_registry.py
  ```
- [ ] All imports record to `import_batches` (`source_version`, `rows_read`, `rows_inserted`, `rows_rejected`, `error_report`)
- [ ] Every import must be **idempotent** (re-running doesn't duplicate records)
- [ ] Source metadata stored on every external record: `source`, `source_version`, `external_id`, `import_batch_id`

---

## Stage 10 — Production Infrastructure *(MEDIUM)*

**Goal**: Scale beyond a single local Flask process.

### What to do
- [ ] Replace in-memory `TTLCache` with **Redis** for shared cache across workers
- [ ] Cache with explicit invalidation triggers (skills change, role reqs change, imports change)
- [ ] Move long-running ops to background workers (Celery or RQ):
  - Resume processing + AI extraction
  - ESCO/O*NET imports
  - Recommendation generation for large profiles
  - Analytics aggregation
- [ ] Add structured logs with request IDs and response latency
- [ ] Add health endpoints: `GET /api/v1/health/live` and `GET /api/v1/health/ready`
- [ ] Production deployment: Nginx → Gunicorn → Flask + Redis + Worker
- [ ] Environment-only config (no secrets in code)
- [ ] Load testing

---

## Stage 11 — Analytics *(MEDIUM)*

**Goal**: Surface meaningful progress and gap insights to students.

### User-level analytics (student-facing)
- Skill growth over time
- Gap reduction trend after reassessment
- Assessment history
- Learning completion and hours spent
- Strongest and weakest skill categories

### What to do
- [ ] `GET /api/v1/students/<id>/analytics` — full personalized report
- [ ] Skill growth chart data (per-skill proficiency over time)
- [ ] Gap reduction timeline (before/after reassessment)
- [ ] Learning completion summary
- [ ] Role readiness trend over time

> **No admin APIs** — data imports and role/skill management stay as CLI commands.

---

## Summary Table

| Stage | Name | Priority | Effort |
|-------|------|----------|--------|
| 0 | Audit & Freeze | ✅ Done | — |
| 1 | Security & Identity | 🔴 CRITICAL | ~1 week |
| 2 | Database & Taxonomy | 🔴 CRITICAL | ~1–2 weeks |
| 3 | Route & Service Architecture | 🟠 HIGH | ~1 week |
| 4 | Skill Assessment System | 🟠 HIGH | ~1 week |
| 5 | Core Skill Intelligence | 🟠 HIGH | ~3–5 days |
| 6 | AI Resume Intelligence | 🟠 HIGH | ~1–2 weeks |
| 7 | Recommendation Intelligence | 🟠 HIGH | ✅ Mostly done |
| 8 | Learning Intelligence | 🟠 HIGH | ~1 week |
| 9 | Data Platform | 🟡 MED/HIGH | ~1 week |
| 10 | Production Infrastructure | 🟡 MEDIUM | ~1 week |
| 11 | Analytics | 🟡 MEDIUM | ~3–5 days |
