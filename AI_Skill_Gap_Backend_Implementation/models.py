"""
SQLAlchemy data models for the AI Skill Gap Prediction System.
Matches the canonical data model specified in PRD Section 14.
"""
from datetime import datetime, timezone
from extensions import db


def _utcnow():
    """Return the current UTC time as a timezone-aware datetime (Python 3.12+ safe)."""
    return datetime.now(timezone.utc)


class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False)
    course = db.Column(db.String(100))
    year = db.Column(db.Integer)
    target_career = db.Column(db.String(200))  # PRD FR-001
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "email": self.email,
            "course": self.course, "year": self.year,
            "target_career": self.target_career,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Skill(db.Model):
    __tablename__ = "skills"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    category = db.Column(db.String(100))   # e.g. Programming, Database, DevOps
    description = db.Column(db.Text)
    source = db.Column(db.String(50), default="CANONICAL")      # ESCO / O*NET / CANONICAL
    source_identifier = db.Column(db.String(500))               # ESCO URI or O*NET element ID

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "category": self.category,
            "description": self.description, "source": self.source
        }


class StudentSkill(db.Model):
    __tablename__ = "student_skills"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    proficiency = db.Column(db.Float, nullable=False, default=0)   # 0–100 scale
    evidence_type = db.Column(
        db.String(50), default="self_reported"
    )  # self_reported | assessment | resume | reassessment | demo
    confidence = db.Column(db.Float, default=1.0)   # 0–1; resume = 0.75, self = 1.0
    updated_at = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow
    )
    __table_args__ = (db.UniqueConstraint("student_id", "skill_id"),)


class Assessment(db.Model):
    __tablename__ = "assessments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False, default=100)
    assessed_at = db.Column(db.DateTime, default=_utcnow)
    attempt_no = db.Column(db.Integer, default=1)


class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    skills_used = db.Column(db.Text)  # Comma-separated skill names (from resume or manual)
    created_at = db.Column(db.DateTime, default=_utcnow)


class Certification(db.Model):
    __tablename__ = "certifications"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    issuer = db.Column(db.String(200))
    issued_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)


class Resume(db.Model):
    __tablename__ = "resumes"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    stored_path = db.Column(db.String(500))
    extracted_text = db.Column(db.Text)
    processing_status = db.Column(
        db.String(50), default="pending"
    )  # pending | processed | failed
    created_at = db.Column(db.DateTime, default=_utcnow)


class SkillEvidence(db.Model):
    """
    Granular evidence for a student skill extracted from resumes, projects, or certifications.
    Includes context snippet (evidence span) and section location.
    """
    __tablename__ = "skill_evidence"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=True)
    raw_term = db.Column(db.String(150), nullable=False)
    evidence_type = db.Column(db.String(50), default="resume")  # resume | project | certification
    source_id = db.Column(db.Integer, nullable=True)            # resume_id, project_id, etc.
    confidence = db.Column(db.Float, default=0.8)
    evidence_span = db.Column(db.Text, nullable=True)          # snippet/sentence where skill was identified
    section = db.Column(db.String(100), nullable=True)         # skills | experience | projects | education | certs
    status = db.Column(db.String(30), default="pending")       # pending | verified | rejected
    created_at = db.Column(db.DateTime, default=_utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "skill_id": self.skill_id,
            "raw_term": self.raw_term,
            "evidence_type": self.evidence_type,
            "source_id": self.source_id,
            "confidence": round(self.confidence, 2) if self.confidence else None,
            "evidence_span": self.evidence_span,
            "section": self.section,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AIExtractionRecord(db.Model):
    """
    Audit record tracking AI extraction pipeline runs, latency, and token/model usage.
    """
    __tablename__ = "ai_extraction_records"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=True, index=True)
    source_type = db.Column(db.String(50), default="resume")
    source_id = db.Column(db.Integer, nullable=True)
    model = db.Column(db.String(100), default="rule-nlp-v1")
    prompt_version = db.Column(db.String(50), default="v1.0")
    latency_ms = db.Column(db.Float, default=0.0)
    token_usage = db.Column(db.Integer, default=0)
    skills_extracted_count = db.Column(db.Integer, default=0)
    unknown_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=_utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "model": self.model,
            "prompt_version": self.prompt_version,
            "latency_ms": round(self.latency_ms, 2) if self.latency_ms else 0.0,
            "token_usage": self.token_usage,
            "skills_extracted_count": self.skills_extracted_count,
            "unknown_count": self.unknown_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class UnknownSkillReview(db.Model):
    """
    Review queue for candidate skill terms that could not be mapped to the canonical catalog.
    Prevents catalog pollution and provides human review queue.
    """
    __tablename__ = "unknown_skill_reviews"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_term = db.Column(db.String(150), nullable=False)
    context_snippet = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(50), default="resume")
    status = db.Column(db.String(30), default="pending_review")  # pending_review | approved | rejected
    suggested_canonical_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "raw_term": self.raw_term,
            "context_snippet": self.context_snippet,
            "source": self.source,
            "status": self.status,
            "suggested_canonical_id": self.suggested_canonical_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class JobRole(db.Model):
    __tablename__ = "job_roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    source = db.Column(db.String(50), nullable=False)         # ESCO | O*NET | DEMO
    source_identifier = db.Column(db.String(500))             # ESCO URI or O*NET SOC code
    description = db.Column(db.Text)
    isco_group = db.Column(db.String(20))                     # ISCO group code (ESCO only)
    onet_code = db.Column(db.String(32), nullable=True)       # O*NET-SOC code (e.g. 15-1252.00)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "source": self.source,
            "source_identifier": self.source_identifier,
            "description": self.description, "isco_group": self.isco_group,
            "onet_code": self.onet_code,
        }


class JobSkill(db.Model):
    __tablename__ = "job_skills"
    id = db.Column(db.Integer, primary_key=True)
    job_role_id = db.Column(db.Integer, db.ForeignKey("job_roles.id", ondelete="CASCADE"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    required_level = db.Column(db.Float, nullable=False, default=50)  # 0–100
    importance = db.Column(db.Float, default=1.0)     # 1.0 = essential, 0.7 = optional
    relation_type = db.Column(db.String(30), default="essential")  # essential | optional
    source = db.Column(db.String(50))                 # ESCO | O*NET | DEMO
    __table_args__ = (db.UniqueConstraint("job_role_id", "skill_id"),)


class Course(db.Model):
    __tablename__ = "courses"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    provider = db.Column(db.String(150))
    description = db.Column(db.Text)
    url = db.Column(db.String(1000))
    difficulty_level = db.Column(db.String(50))  # Beginner | Intermediate | Advanced
    rating = db.Column(db.Float, default=0.0)    # 0–5 scale
    source = db.Column(db.String(50), default="Coursera")

    def to_dict(self):
        return {
            "id": self.id, "title": self.title, "provider": self.provider,
            "description": self.description, "url": self.url,
            "difficulty_level": self.difficulty_level, "rating": self.rating
        }


class CourseSkill(db.Model):
    __tablename__ = "course_skills"
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    relevance = db.Column(db.Float, default=1.0)   # 0–1; how strongly this course covers the skill


class SkillGap(db.Model):
    __tablename__ = "skill_gaps"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    job_role_id = db.Column(db.Integer, db.ForeignKey("job_roles.id", ondelete="CASCADE"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    current_level = db.Column(db.Float, nullable=False)
    required_level = db.Column(db.Float, nullable=False)
    gap_value = db.Column(db.Float, nullable=False)
    gap_percent = db.Column(db.Float, nullable=False)
    severity = db.Column(db.String(20), nullable=False)     # LOW | MEDIUM | HIGH
    priority_score = db.Column(db.Float, nullable=False)
    evidence_summary = db.Column(db.String(255), nullable=True)
    evidence_factor = db.Column(db.Float, default=1.0)
    explanation = db.Column(db.Text, nullable=True)
    model_version = db.Column(db.String(100), default="deterministic-baseline-v1")
    created_at = db.Column(db.DateTime, default=_utcnow)

    def to_dict(self, skill_name=None, role_name=None):
        return {
            "skill_id": self.skill_id,
            "skill": skill_name,
            "current_level": self.current_level,
            "required_level": self.required_level,
            "gap": self.gap_value,
            "gap_percent": self.gap_percent,
            "severity": self.severity,
            "priority_score": self.priority_score,
            "evidence_summary": self.evidence_summary,
            "evidence_factor": self.evidence_factor,
            "explanation": self.explanation,
            "model_version": self.model_version,
        }


class Recommendation(db.Model):
    __tablename__ = "recommendations"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"))
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(1000))
    score = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=_utcnow)


class RecommendationRun(db.Model):
    """
    Snapshot of a recommendation generation run.
    Ensures recommendation results are reproducible over time, auditable, and traceable.
    """
    __tablename__ = "recommendation_runs"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    job_role_id = db.Column(db.Integer, db.ForeignKey("job_roles.id"), nullable=True)
    weights_used = db.Column(db.JSON, nullable=False)
    total_recommendations = db.Column(db.Integer, default=0)
    recommendations_snapshot = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "job_role_id": self.job_role_id,
            "weights_used": self.weights_used,
            "total_recommendations": self.total_recommendations,
            "recommendations_snapshot": self.recommendations_snapshot,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LearningProgress(db.Model):
    __tablename__ = "learning_progress"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"))
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"))
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(
        db.String(30), default="not_started"
    )  # not_started | in_progress | completed
    completion = db.Column(db.Float, default=0)   # 0–100
    updated_at = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow
    )


class Reassessment(db.Model):
    __tablename__ = "reassessments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    old_level = db.Column(db.Float)
    new_level = db.Column(db.Float)
    improvement = db.Column(db.Float)   # new_level - old_level (computed on save)
    evidence_type = db.Column(db.String(50), default="reassessment")
    assessed_at = db.Column(db.DateTime, default=_utcnow)


# ──────────────────────────────────────────────────────────────────────────────
# Auth
# ──────────────────────────────────────────────────────────────────────────────
class User(db.Model):
    """
    Authentication account — linked 1:1 to a Student profile.
    Keeps auth (password hashes) separate from academic data.
    """
    __tablename__ = "users"
    id            = db.Column(db.Integer, primary_key=True)
    email         = db.Column(db.String(180), unique=True, nullable=False)
    name          = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role          = db.Column(db.String(30), default="student")    # student | admin
    student_id    = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="SET NULL"), nullable=True)
    created_at    = db.Column(db.DateTime, default=_utcnow)
    last_login    = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id":         self.id,
            "name":       self.name,
            "email":      self.email,
            "role":       self.role,
            "student_id": self.student_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat()  if self.last_login  else None,
        }


# ──────────────────────────────────────────────────────────────────────────────
# Personalized Learning Path
# ──────────────────────────────────────────────────────────────────────────────
class LearningPath(db.Model):
    """
    A generated, ordered learning roadmap for a student targeting a specific role.
    Regenerated each time POST /students/<id>/learning-path is called.
    """
    __tablename__ = "learning_paths"
    id               = db.Column(db.Integer, primary_key=True)
    student_id       = db.Column(db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"),  nullable=False)
    job_role_id      = db.Column(db.Integer, db.ForeignKey("job_roles.id", ondelete="CASCADE"), nullable=False)
    total_courses    = db.Column(db.Integer, default=0)
    total_hours      = db.Column(db.Integer, default=0)
    match_score_at_generation = db.Column(db.Float, default=0.0)
    created_at       = db.Column(db.DateTime, default=_utcnow)
    __table_args__   = (db.UniqueConstraint("student_id", "job_role_id"),)


class LearningPathStep(db.Model):
    """
    A single step (course) within a LearningPath.
    step_order determines the sequence; phase groups steps into phases.
    """
    __tablename__  = "learning_path_steps"
    id             = db.Column(db.Integer, primary_key=True)
    path_id        = db.Column(db.Integer, db.ForeignKey("learning_paths.id", ondelete="CASCADE"), nullable=False)
    step_order     = db.Column(db.Integer, nullable=False)   # 1, 2, 3, ...
    course_id      = db.Column(db.Integer, db.ForeignKey("courses.id"),   nullable=False)
    skill_id       = db.Column(db.Integer, db.ForeignKey("skills.id"),    nullable=False)
    phase          = db.Column(db.String(10), nullable=False)  # HIGH | MEDIUM | LOW
    estimated_hours = db.Column(db.Integer, default=25)


# ─────────────────────────────────────────────────────────────────────────────
# Data Import Tracking
# ─────────────────────────────────────────────────────────────────────────────
class ImportBatch(db.Model):
    """
    Records every CLI data import run (sync-roles, seed-courses, ingest-onet).
    Enables tracking what data was loaded and when.
    """
    __tablename__ = "import_batches"
    id            = db.Column(db.Integer, primary_key=True)
    source        = db.Column(db.String(100), nullable=False)  # sync_15_roles | seed_courses | onet
    started_at    = db.Column(db.DateTime, default=_utcnow)
    completed_at  = db.Column(db.DateTime, nullable=True)
    status        = db.Column(db.String(20), default="running")  # running | success | failed
    rows_inserted = db.Column(db.Integer, default=0)
    rows_updated  = db.Column(db.Integer, default=0)
    rows_skipped  = db.Column(db.Integer, default=0)
    error_summary = db.Column(db.Text, nullable=True)

    def finish(self, inserted=0, updated=0, skipped=0, error=None):
        """Mark this batch as completed (call at end of CLI import)."""
        self.completed_at  = _utcnow()
        self.status        = "failed" if error else "success"
        self.rows_inserted = inserted
        self.rows_updated  = updated
        self.rows_skipped  = skipped
        self.error_summary = str(error) if error else None

    def to_dict(self):
        return {
            "id":           self.id,
            "source":       self.source,
            "started_at":   self.started_at.isoformat()   if self.started_at   else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status":       self.status,
            "rows_inserted": self.rows_inserted,
            "rows_updated":  self.rows_updated,
            "rows_skipped":  self.rows_skipped,
            "error_summary": self.error_summary,
        }
