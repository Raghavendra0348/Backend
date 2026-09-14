"""
SQLAlchemy data models for the AI Skill Gap Prediction System.
Matches the canonical data model specified in PRD Section 14.
"""
from datetime import datetime
from extensions import db


class Student(db.Model):
    __tablename__ = "students"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False)
    course = db.Column(db.String(100))
    year = db.Column(db.Integer)
    target_career = db.Column(db.String(200))  # PRD FR-001
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    proficiency = db.Column(db.Float, nullable=False, default=0)   # 0–100 scale
    evidence_type = db.Column(
        db.String(50), default="self_reported"
    )  # self_reported | assessment | resume | reassessment | demo
    confidence = db.Column(db.Float, default=1.0)   # 0–1; resume = 0.75, self = 1.0
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    __table_args__ = (db.UniqueConstraint("student_id", "skill_id"),)


class Assessment(db.Model):
    __tablename__ = "assessments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False, default=100)
    assessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    attempt_no = db.Column(db.Integer, default=1)


class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    skills_used = db.Column(db.Text)  # Comma-separated skill names (from resume or manual)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Certification(db.Model):
    __tablename__ = "certifications"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    issuer = db.Column(db.String(200))
    issued_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)


class Resume(db.Model):
    __tablename__ = "resumes"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    stored_path = db.Column(db.String(500))
    extracted_text = db.Column(db.Text)
    processing_status = db.Column(
        db.String(50), default="pending"
    )  # pending | processed | failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class JobRole(db.Model):
    __tablename__ = "job_roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    source = db.Column(db.String(50), nullable=False)         # ESCO | O*NET | DEMO
    source_identifier = db.Column(db.String(500))             # ESCO URI or O*NET SOC code
    description = db.Column(db.Text)
    isco_group = db.Column(db.String(20))                     # ISCO group code (ESCO only)

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "source": self.source,
            "source_identifier": self.source_identifier,
            "description": self.description, "isco_group": self.isco_group
        }


class JobSkill(db.Model):
    __tablename__ = "job_skills"
    id = db.Column(db.Integer, primary_key=True)
    job_role_id = db.Column(db.Integer, db.ForeignKey("job_roles.id"), nullable=False)
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
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    relevance = db.Column(db.Float, default=1.0)   # 0–1; how strongly this course covers the skill


class SkillGap(db.Model):
    __tablename__ = "skill_gaps"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    job_role_id = db.Column(db.Integer, db.ForeignKey("job_roles.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    current_level = db.Column(db.Float, nullable=False)
    required_level = db.Column(db.Float, nullable=False)
    gap_value = db.Column(db.Float, nullable=False)
    gap_percent = db.Column(db.Float, nullable=False)
    severity = db.Column(db.String(20), nullable=False)     # LOW | MEDIUM | HIGH
    priority_score = db.Column(db.Float, nullable=False)
    model_version = db.Column(db.String(100), default="deterministic-baseline-v1")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
            "model_version": self.model_version
        }


class Recommendation(db.Model):
    __tablename__ = "recommendations"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"))
    title = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(1000))
    score = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class LearningProgress(db.Model):
    __tablename__ = "learning_progress"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"))
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"))
    title = db.Column(db.String(255), nullable=False)
    status = db.Column(
        db.String(30), default="not_started"
    )  # not_started | in_progress | completed
    completion = db.Column(db.Float, default=0)   # 0–100
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Reassessment(db.Model):
    __tablename__ = "reassessments"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    old_level = db.Column(db.Float)
    new_level = db.Column(db.Float)
    improvement = db.Column(db.Float)   # new_level - old_level (computed on save)
    evidence_type = db.Column(db.String(50), default="reassessment")
    assessed_at = db.Column(db.DateTime, default=datetime.utcnow)
