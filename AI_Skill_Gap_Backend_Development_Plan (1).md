# AI-Based Skill Gap Platform — Deep Backend Development & Improvement Plan

Repository analyzed:
`https://github.com/Raghavendra0348/Backend`

Analysis scope:

- Flask application factory and configuration
- JWT authentication
- SQLAlchemy models
- REST API routes
- skill normalization
- resume parsing
- skill-gap engine
- role matching
- course recommendation
- learning-path generation
- cache layer
- ESCO/O*NET ingestion
- ML training pipeline
- requirements and project documentation

## 1. Executive Assessment

The repository already contains a strong prototype foundation. It is not an empty backend.

Current major capabilities visible in the repository:

- Flask API and application factory
- JWT authentication
- SQLAlchemy data models
- Student profile and skill management
- Skill-gap computation
- Role matching
- Course recommendation
- Resume PDF/DOCX extraction
- Skill alias normalization
- Learning-path generation
- Progress and reassessment tracking
- ESCO/O*NET ingestion
- ML model training/inference
- In-memory caching
- Automated tests

The main objective now should NOT be to add random features.

The objective should be to turn the current prototype into a:

- clean
- normalized
- secure
- explainable
- testable
- scalable
- AI-enhanced
- production-ready
  backend.

## 2. Most Important Findings

### CRITICAL

1. Authentication and student identity are split across `User` and `Student`.

   - This creates duplicated identity data and risks authorization mistakes.
   - Protected user-facing APIs should derive the student identity from the authenticated user rather than trusting arbitrary `<sid>` path values.
2. Many student APIs are not visibly protected by JWT.

   - The authentication module exists, but the main student routes shown do not consistently enforce authorization.
   - This must be fixed before production.
3. Skill normalization can create a new skill record from arbitrary input.

   - `_resolve_skill_id()` can create a `Skill` with `source="MANUAL"` when a name is not found.
   - For a controlled skill-gap platform, this should become a review/unknown-skill workflow rather than silently expanding the canonical catalog.
4. Resume extraction is primarily rule/keyword based.

   - This is useful as a baseline but is not sufficient for strong AI-based resume intelligence.
   - The next layer should produce structured entities, canonical skill IDs, evidence spans, confidence, and verification state.
5. The ML model currently predicts gap severity after the deterministic gap percentage is already computed.

   - This makes the ML problem close to reproducing a threshold-based label.
   - The ML layer should be moved toward higher-value tasks such as skill extraction, role similarity, evidence confidence, course ranking, and personalized learning-path optimization.
   - Keep deterministic gap math as the authoritative baseline.
6. Data taxonomy is mixed.

   - Practical technical skills, ESCO skills, O*NET knowledge, and O*NET work activities are stored close to the same `Skill` concept.
   - This should be represented explicitly with taxonomy/source/type fields and mapping tables.

### HIGH

7. `routes.py` is very large and contains business logic directly inside HTTP handlers.

   - Split routes into blueprints/controllers by module and move logic into services.
8. Database schema is missing important lifecycle/audit concepts.

   - Add timestamps, source metadata, verification state, assessment history, AI extraction records, recommendation snapshots, and dataset import tracking.
9. Learning progress is currently modeled as repeated rows.

   - A user learning enrollment/progress entity should have a stable unique record per course/resource, with history tracked separately if needed.
10. Recommendations are persisted broadly and then replaced.

    - Introduce recommendation runs/snapshots so recommendations can be reproduced and compared over time.
11. Cache is process-local.

    - `cachetools.TTLCache` is fine for development but does not provide shared cache semantics across multiple production workers.
12. Dataset import should be treated as a formal data pipeline.

    - Add import job tracking, validation reports, deduplication, row counts, failures, source versions, and idempotent import keys.
13. The project documentation contains completion claims that are stronger than the code currently justifies.

    - Treat the repository as a working prototype, not as a final production implementation.

## 3. Target Architecture

Recommended target:

```
src/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── errors.py
│   └── logging.py
│
├── api/
│   ├── auth/
│   ├── users/
│   ├── skills/
│   ├── roles/
│   ├── assessments/
│   ├── resumes/
│   ├── skill_gap/
│   ├── recommendations/
│   ├── learning/
│   ├── analytics/
│   ├── inadmin/
│   └── health/
│
├── domain/
│   ├── users/
│   ├── skills/
│   ├── roles/
│   ├── assessments/
│   ├── skill_gap/
│   ├── recommendations/
│   └── learning/
│
├── models/
│
├── repositories/
│
├── integrations/
│   ├── ai/
│   ├── esco/
│   ├── onet/
│   └── learning_catalog/
│
├── workers/
│
├── schemas/
│
├── utils/
│
└── migrations/
```

Do not restructure everything in one commit. Migrate module by module.

## 4. Database Redesign

### 4.1 Users

Keep:

- users
- user_profiles

Change the current one-to-one relationship so the authenticated account becomes the source of identity.

Recommended core fields:

```
users
- id
- email
- password_hash
- role
- is_active
- email_verified
- created_at
- updated_at
- last_login_at
```

```
user_profiles
- user_id
- full_name
- course
- academic_year
- graduation_year
- target_role_id
- created_at
- updated_at
```

### 4.2 Canonical Skills

Recommended:

```
skills
- id
- canonical_name
- slug
- description
- category_id
- skill_type
- status
- created_at
- updated_at
```

```
skill_aliases
- id
- skill_id
- alias
- normalized_alias
- source
- confidence
```

```
skill_categories
- id
- name
- parent_id
```

Do not silently create canonical skills from arbitrary user text.

### 4.3 External Taxonomies

Use explicit source tables/mappings:

```
external_skills
- id
- source
- external_id
- label
- description
```

```
external_skill_mappings
- id
- external_skill_id
- canonical_skill_id
- mapping_confidence
- mapping_method
```

Do the same for occupations.

### 4.4 Roles

```
roles
- id
- canonical_name
- slug
- description
- status
- created_at
- updated_at
```

```
role_aliases
- id
- role_id
- alias
```

```
role_skills
- role_id
- skill_id
- required_level
- importance_weight
- relation_type
- source
```

## 5. Skill Evidence Model

The current `StudentSkill` should be expanded.

Recommended:

```
user_skills
- id
- user_id
- skill_id
- proficiency_level
- confidence_score
- verification_status
- primary_source
- years_experience
- last_assessed_at
- created_at
- updated_at
```

Evidence:

```
skill_evidence
- id
- user_skill_id
- evidence_type
- source_id
- evidence_text
- evidence_score
- created_at
```

Evidence types:

- self_reported
- assessment
- resume
- project
- certification
- ai_inferred
- verified

This allows the backend to distinguish:
“User says they know React”
from
“Resume + assessment + project evidence support React.”

## 6. Proficiency System

Use one consistent scale.

Recommended:

```
0 = none
1 = beginner
2 = basic
3 = intermediate
4 = advanced
5 = expert
```

If the internal database keeps 0–100, define a single conversion layer.

Do not mix 0–5 and 0–100 without an explicit conversion function.

## 7. Skill Gap Engine

Keep the deterministic engine as the source of truth.

For each required skill:

```
gap = max(required_level - current_level, 0)
```

Then:

```
normalized_gap = gap / required_level
```

Priority:

```
priority =
    normalized_gap
    × importance_weight
    × evidence_adjustment
```

Output should include:

- current level
- required level
- gap
- gap percentage
- severity
- priority
- evidence
- explanation
- model/version used

Do not make an LLM responsible for the actual gap arithmetic.

## 8. Role Recommendation Engine

Evaluate all target roles.

For each role return:

```
role_id
role_name
match_score
core_skill_coverage
weighted_skill_coverage
missing_core_skills
weak_skills
strong_skills
explanation
```

Recommended score:

```
role_score =
Σ(min(user_level, required_level) × weight)
/
Σ(required_level × weight)
× 100
```

Add a separate confidence score based on how much of the user's profile is verified.

Avoid presenting a high score as “job ready” solely from self-reported skills.

## 9. Resume Intelligence — Major AI Upgrade

Replace the current simple keyword pipeline with:

```
Resume File
   ↓
Text Extraction
   ↓
Section Detection
   ↓
Entity Extraction
   ↓
Skill Extraction
   ↓
Skill Normalization
   ↓
Canonical Skill Mapping
   ↓
Evidence Extraction
   ↓
Confidence Scoring
   ↓
Human/User Verification
   ↓
User Skill Profile
```

Structured extraction should identify:

- skills
- programming languages
- frameworks
- tools
- databases
- cloud platforms
- job roles
- years of experience
- projects
- education
- certifications

For every extracted skill store:

```
skill_id
raw_text
normalized_skill_id
confidence
evidence_span
section
source
verification_status
```

AI output must be validated against the canonical skill catalog before persistence.

## 10. AI Skill Normalization

The current alias map is useful, but it should evolve into a layered strategy:

```
1. Exact canonical match
2. Alias match
3. Normalized string match
4. External taxonomy match
5. Embedding similarity
6. LLM verification
7. Unknown/review state
```

Example:

```
"Postgres"
    ↓
"PostgreSQL"
    ↓
canonical_skill_id = 42
```

Do not immediately add “Postgres” as a new canonical skill.

## 11. ESCO / O*NET Architecture

Treat ESCO and O*NET as source taxonomies.

The internal model should be:

```
ESCO/O*NET
     ↓
External Occupation
     ↓
External Skill
     ↓
Mapping Layer
     ↓
Canonical Skill / Canonical Role
```

Keep source metadata:

```
source
source_version
external_id
external_uri
import_batch_id
```

This lets you update datasets later without destroying the canonical model.

## 12. Data Ingestion Pipeline

Turn `data/ingest.py` into separate pipeline components:

```
ingestion/
├── esco_importer.py
├── onet_importer.py
├── course_importer.py
├── student_importer.py
├── normalizer.py
├── validator.py
└── importer_registry.py
```

Add:

```
import_batches
- id
- source
- source_version
- started_at
- completed_at
- status
- rows_read
- rows_inserted
- rows_updated
- rows_rejected
- error_report
```

Every import must be idempotent.

## 13. Assessments

The current assessment system is too simple for a full platform.

Create:

```
assessment_templates
assessment_questions
assessment_question_skills
assessment_attempts
assessment_answers
skill_assessment_results
```

This allows:

- skill-specific tests
- different question difficulties
- adaptive assessment later
- score normalization
- attempt history
- confidence estimation

## 14. Learning System

Replace simple progress logging with:

```
learning_resources
resource_skills
learning_paths
learning_path_steps
user_learning_enrollments
learning_progress_events
```

Track:

- enrolled
- started
- progress %
- completed
- started_at
- completed_at
- time_spent

Keep event history separately from the current aggregate progress.

## 15. Recommendation System

Current TF-IDF recommendation is a useful baseline.

Recommended future ranking pipeline:

```
Candidate Generation
    ↓
Skill Coverage
    ↓
Gap Priority
    ↓
Difficulty Fit
    ↓
Content Similarity
    ↓
User Preferences
    ↓
Rating / Quality
    ↓
Diversity
    ↓
Final Ranking
```

Potential score:

```
final_score =
0.35 skill_gap_relevance
+ 0.20 learning_level_fit
+ 0.15 content_similarity
+ 0.10 quality
+ 0.10 user_preference
+ 0.10 diversity
```

Keep weights configurable.

## 16. Personalized Learning Path

The current learning path is severity-based only.

Upgrade it to dependency-aware ordering.

Example:

```
JavaScript
   ↓
TypeScript
   ↓
React
   ↓
State Management
   ↓
Testing
   ↓
Frontend Architecture
```

Path generation should consider:

- prerequisite skills
- current proficiency
- gap severity
- importance
- estimated effort
- learning-resource quality
- completed resources

## 17. Authentication & Authorization

Protect all student-private endpoints.

Rules:

```
User can:
- read/update own profile
- manage own skills
- manage own evidence
- upload own resume
- view own gaps
- view own recommendations
- manage own learning progress
```

Never trust:

```
/students/<sid>
```

as authorization.

Resolve the authenticated user's student/profile ID server-side.

## 18. Security Improvements

Implement:

- centralized authentication middleware
- role-based authorization
- password policy
- refresh-token rotation if applicable
- token revocation strategy
- strict CORS
- secure file upload validation
- file type/content validation
- storage outside public web root
- rate limiting
- request size limits
- security headers
- structured audit logs
- secret management
- generic production errors

Never return raw exception messages to clients in production.

## 19. API Architecture

Version the API:

```
/api/v1/
```

Suggested modules:

```
/api/v1/auth/*
/api/v1/users/*
/api/v1/skills/*
/api/v1/roles/*
/api/v1/assessments/*
/api/v1/resumes/*
/api/v1/skill-gap/*
/api/v1/recommendations/*
/api/v1/learning/*
/api/v1/analytics/*
```

Use a consistent envelope:

```
{
  "success": true,
  "data": {...},
  "meta": {...}
}
```

Errors:

```
{
  "success": false,
  "error": {
    "code": "SKILL_NOT_FOUND",
    "message": "Skill not found"
  }
}
```

## 20. Validation

Introduce a schema validation layer.

Validate:

- JSON requests
- query params
- path params
- file uploads
- enums
- numeric ranges
- email
- IDs
- pagination

Do not duplicate ad hoc validation logic across routes.

## 21. Route Refactoring

`routes.py` should be split.

Target:

```
api/
├── students.py
├── skills.py
├── roles.py
├── assessments.py
├── resumes.py
├── gap_analysis.py
├── recommendations.py
├── learning.py
└── analytics.py
```

Routes should mostly perform:

```
request
→ validation
→ service call
→ response
```

No heavy business logic.

## 22. Service Layer

Use services for:

```
UserService
SkillService
RoleService
AssessmentService
ResumeService
SkillGapService
RecommendationService
LearningPathService
AnalyticsService
TaxonomyService
```

Use repositories for complex database operations.

## 23. Caching

Current in-memory `TTLCache` is acceptable for local development.

For production:

```
Redis
```

Cache candidates:

- role list
- role skills
- skill search
- course search
- computed role matches
- gap analysis results
- recommendation results

Add cache invalidation when:

- user skills change
- role requirements change
- course mappings change
- taxonomy imports change

## 24. Background Jobs

Move expensive operations out of HTTP requests:

- resume processing
- AI extraction
- ESCO imports
- O*NET imports
- course imports
- recommendation generation for large profiles
- analytics aggregation

Recommended architecture:

```
API
 ↓
Job Queue
 ↓
Worker
 ↓
Database
```

Use Celery/RQ/another suitable queue only if operational complexity is justified.

## 25. AI Architecture

Create an AI provider abstraction:

```
integrations/ai/
├── base.py
├── provider.py
├── resume_extractor.py
├── skill_normalizer.py
├── career_explainer.py
└── learning_path_generator.py
```

Never scatter AI API calls through route files.

Each AI request should have:

```
prompt_version
model
input_hash
status
latency
token usage if available
created_at
```

## 26. AI Guardrails

AI may assist with:

- extraction
- normalization
- explanation
- semantic matching
- learning path suggestions

AI should not directly decide:

- user authorization
- database ownership
- password validation
- permission checks
- core numerical gap calculation
- data integrity constraints

## 27. AI Explainability

Every AI recommendation should be traceable.

Example:

```
Recommendation:
Backend Developer

Reasons:
- 9/15 core skills have sufficient proficiency
- Strong PostgreSQL and REST API skills
- Main gaps are Redis, Docker, Microservices
- Resume evidence supports Node.js and API development
```

Do not return a score without an explanation.

## 28. Analytics

Add backend analytics:

### User-level

- skill growth
- gap reduction
- assessment trend
- learning completion
- strongest skill categories

### System-level

- popular roles
- common gaps
- highest-demand skills
- recommendation click/use rates
- learning completion rates
- extraction confidence distribution

## 29. Auditability

Add audit logs for:

- login
- profile changes
- skill changes
- assessment submission
- resume processing
- AI extraction
- recommendation generation
- taxonomy import

## 30. Testing Strategy

Required levels:

### Unit

- proficiency conversion
- gap computation
- score calculation
- normalization
- ranking

### Integration

- authentication
- authorization
- role retrieval
- skill management
- resume flow
- assessments
- recommendations

### End-to-End

Test complete journey:

```
Register
→ Login
→ Build profile
→ Upload resume
→ Confirm skills
→ Take assessment
→ Select target role
→ Analyze gap
→ Receive recommendations
→ Generate learning path
→ Complete learning
→ Reassess
→ Observe updated gap
```

## 31. Data Quality Tests

Add tests for:

- duplicate canonical skills
- duplicate role-skill mappings
- missing taxonomy mappings
- invalid required levels
- invalid weights
- orphan records
- repeated imports
- broken course URLs if validation is available

## 32. Observability

Add:

- structured logs
- request IDs
- response latency
- error counters
- AI latency
- import metrics
- database query monitoring

Health endpoints:

```
/api/v1/health/live
/api/v1/health/ready
```

Readiness should verify critical dependencies.

## 33. Deployment

Production architecture should support:

```
Reverse Proxy
      ↓
Flask/Gunicorn
      ↓
Application
 ┌────┼───────────┐
 DB  Redis      Worker
```

Configuration through environment variables only.

## 34. Priority Roadmap

### Phase 0 — Audit & Freeze

Priority: CRITICAL

- Freeze existing behavior.
- Add regression tests.
- Document current endpoints.
- Capture baseline database counts.
- Identify breaking API differences.

### Phase 1 — Security & Identity

Priority: CRITICAL

- JWT enforcement
- ownership checks
- admin RBAC
- validation
- centralized errors

### Phase 2 — Database & Taxonomy

Priority: CRITICAL

- canonical skill model
- aliases
- role/skill mappings
- ESCO/O*NET mapping layer
- evidence model
- migration system

### Phase 3 — Service Architecture

Priority: HIGH

- split routes
- create service layer
- repositories
- schemas
- centralized response handling

### Phase 4 — Skill Assessment

Priority: HIGH

- assessment templates
- questions
- attempts
- normalized scoring
- evidence/confidence

### Phase 5 — Core Skill Intelligence

Priority: HIGH

- deterministic gap engine
- role matcher
- explainable prioritization
- role-readiness computation

### Phase 6 — AI Resume Intelligence

Priority: HIGH

- structured extraction
- canonical mapping
- evidence spans
- confidence
- user verification

### Phase 7 — Recommendation Intelligence

Priority: HIGH

- improved course ranking
- user context
- diversity
- personalization

### Phase 8 — Learning Intelligence

Priority: HIGH

- prerequisite graph
- path generation
- resource tracking
- progress events
- reassessment loop

### Phase 9 — Data Platform

Priority: MEDIUM/HIGH

- formal ESCO/O*NET import jobs
- import history
- validation reports
- versioning

### Phase 10 — Production Infrastructure

Priority: MEDIUM

- Redis
- background workers
- observability
- deployment hardening
- load testing

## 35. What To Keep From The Existing Project

KEEP and evolve:

- Flask application factory
- SQLAlchemy
- JWT
- bcrypt
- deterministic gap engine
- role matcher
- resume parser baseline
- learning path concept
- ESCO/O*NET ingestion concept
- testing structure
- cache abstraction

## 36. What To Refactor

REFACTOR:

- `routes.py`
- `models.py`
- skill normalization
- resume extraction
- ingestion pipeline
- recommendation ranking
- authentication ownership checks
- learning progress model
- cache usage
- AI/ML boundaries

## 37. What To Add

ADD:

- API versioning
- schema validation
- migrations
- service/repository layers
- skill evidence
- assessment system
- taxonomy mapping
- AI extraction records
- recommendation runs
- learning enrollment
- audit logs
- import batches
- observability
- background jobs
- Redis support

## 38. What To Avoid

Do NOT add complexity just to make the project look advanced.

Avoid:

- microservices too early
- multiple databases without need
- LLM-driven core business logic
- duplicate taxonomies
- uncontrolled skill creation
- arbitrary AI scores
- synchronous long-running imports
- giant route/controller files

## 39. Final Target Product Flow

The finished backend should support:

```
USER
 ↓
Profile
 ↓
Skills + Resume + Projects + Certifications
 ↓
AI Skill Extraction
 ↓
Canonical Skill Mapping
 ↓
Assessment
 ↓
Verified Skill Profile
 ↓
Select / Recommend Career Roles
 ↓
Role Match
 ↓
Skill Gap Analysis
 ↓
Priority Gaps
 ↓
Course/Resource Recommendation
 ↓
Personalized Learning Path
 ↓
Learning Progress
 ↓
Reassessment
 ↓
Updated Skill Profile
 ↓
Updated Role Readiness
```

## 40. Final Definition of Done

The backend is ready for real frontend integration only when:

- Authentication is enforced everywhere required.
- Users cannot access another user's private resources.
- Skills are canonical and deduplicated.
- ESCO/O*NET are mapped rather than duplicated blindly.
- Resume extraction produces structured evidence.
- Skill gaps are deterministic and explainable.
- Role recommendations have transparent scoring.
- AI is used for high-value semantic tasks.
- Learning paths use prerequisites and gap priority.
- Learning progress is persistent and auditable.
- Data imports are versioned and idempotent.
- APIs are versioned and validated.
- Errors are standardized.
- Tests cover core business logic.
- Logs and health checks exist.
- Production configuration is separated from development.
- The system can scale beyond a single local Flask process.

## Recommended implementation order

1. Security and identity
2. Database/taxonomy cleanup
3. Route/service refactor
4. Assessment system
5. Deterministic skill-gap engine
6. AI resume/skill intelligence
7. Role recommendation
8. Course recommendation
9. Learning path and progress
10. ESCO/O*NET pipeline hardening
11. Admin + analytics
12. Redis/background jobs/observability
13. Production deployment and load testing
