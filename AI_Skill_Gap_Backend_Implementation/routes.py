"""
routes.py — Complete REST API blueprint for the AI Skill Gap System.

Endpoints (PRD Section 17 + Guide Section 15):
  GET  /api/health
  GET  /api/skills                          — Skill catalogue with search
  POST /api/students                        — Create student
  GET  /api/students/<id>                   — Get student + skills
  PUT  /api/students/<id>                   — Update student profile
  POST /api/students/<id>/skills            — Add/update skill proficiency
  POST /api/students/<id>/assessments       — Submit assessment (updates proficiency)
  POST /api/students/<id>/projects          — Add project
  POST /api/students/<id>/certifications    — Add certification
  POST /api/students/<id>/resume            — Upload & parse resume
  GET  /api/roles                           — List target job roles
  GET  /api/roles/<id>/skills               — Required skills for a role
  POST /api/skill-gap/analyze               — Run gap analysis (student + role)
  GET  /api/students/<id>/gaps              — Retrieve persisted gaps (with role_id param)
  GET  /api/students/<id>/recommendations   — Get top-K recommendations
  POST /api/students/<id>/progress          — Record learning progress
  POST /api/students/<id>/reassessment      — Submit reassessment + recalculate
  GET  /api/students/<id>/dashboard         — Full dashboard summary
  --- NEW ---
  GET  /api/students/<id>/role-match        — Job role match score (all roles or one)
  POST /api/students/<id>/learning-path     — Generate personalized learning path
  GET  /api/students/<id>/learning-path     — Retrieve saved learning path
  GET  /api/students/<id>/analytics         — Skill progress analytics & trends
  GET  /api/cache/stats                     — Cache statistics (debug)
"""
import logging
from pathlib import Path

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from extensions import db
from models import (
    Assessment, Certification, Course, CourseSkill, JobRole, JobSkill,
    LearningProgress, Project, Reassessment, Recommendation, Resume,
    Skill, SkillGap, Student, StudentSkill,
)
from services.gap_engine import analyze
from services.recommender import recommend
from services.resume_parser import (
    candidate_skills, extract_certifications_text,
    extract_projects_text, extract_text,
)
import cache as _cache
from services.role_matcher import compute_role_match
from services.learning_path import generate_learning_path, get_learning_path
from services.analytics import compute_analytics

log = logging.getLogger(__name__)
api = Blueprint("api", __name__)

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
VALID_PROGRESS_STATUSES = ("not_started", "in_progress", "completed")


# ──────────────────────────────────────────────────────────────────────────────
# Health
# ──────────────────────────────────────────────────────────────────────────────
@api.get("/health")
def health():
    """Backend health check."""
    return jsonify({"status": "ok"})


# ──────────────────────────────────────────────────────────────────────────────
# Skills catalogue
# ──────────────────────────────────────────────────────────────────────────────
@api.get("/skills")
def list_skills():
    """
    List all canonical skills.
    Optional query params:
      ?search=<text>     — filter by name (case-insensitive substring)
      ?category=<cat>    — filter by exact category
      ?limit=<int>       — max results (default 100, max 500)
    """
    search   = (request.args.get("search") or "").strip()
    category = (request.args.get("category") or "").strip()
    limit    = min(int(request.args.get("limit", 100)), 500)

    q = Skill.query
    if search:
        q = q.filter(Skill.name.ilike(f"%{search}%"))
    if category:
        q = q.filter(Skill.category == category)
    skills = q.order_by(Skill.name).limit(limit).all()

    # Also return distinct categories for UI dropdowns
    categories = [
        r[0] for r in
        db.session.query(Skill.category).distinct().order_by(Skill.category).all()
        if r[0]
    ]
    return jsonify({
        "total": len(skills),
        "categories": categories,
        "skills": [s.to_dict() for s in skills],
    })


# ──────────────────────────────────────────────────────────────────────────────
# Students
# ──────────────────────────────────────────────────────────────────────────────
@api.post("/students")
def create_student():
    """FR-001 — Create a student profile."""
    d = request.get_json() or {}
    name  = (d.get("name") or "").strip()
    email = (d.get("email") or "").strip()
    if not name or not email:
        return jsonify({"error": "name and email are required"}), 400
    if Student.query.filter_by(email=email).first():
        return jsonify({"error": "email already registered"}), 409

    s = Student(
        name=name, email=email,
        course=d.get("course"), year=d.get("year"),
        target_career=d.get("target_career"),
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({"id": s.id, "name": s.name}), 201


@api.get("/students")
def list_students():
    """List recent students (up to limit, default 50)."""
    limit = min(int(request.args.get("limit", 50)), 100)
    students = Student.query.order_by(Student.id.desc()).limit(limit).all()
    return jsonify([s.to_dict() for s in students])


@api.get("/students/<int:sid>")
def get_student(sid):
    """Get student profile with current skills."""
    s = db.session.get(Student, sid)
    if not s:
        return jsonify({"error": "student not found"}), 404

    rows = (
        db.session.query(StudentSkill, Skill)
        .join(Skill, Skill.id == StudentSkill.skill_id)
        .filter(StudentSkill.student_id == sid)
        .all()
    )
    return jsonify({
        **s.to_dict(),
        "skills": [
            {
                "skill_id":     sk.id,
                "skill":        sk.name,
                "category":     sk.category,
                "proficiency":  ss.proficiency,
                "evidence_type": ss.evidence_type,
                "confidence":   ss.confidence,
            }
            for ss, sk in rows
        ],
    })


@api.put("/students/<int:sid>")
def update_student(sid):
    """Update student profile fields."""
    s = db.session.get(Student, sid)
    if not s:
        return jsonify({"error": "student not found"}), 404
    d = request.get_json() or {}
    for field in ("name", "course", "year", "target_career"):
        if field in d:
            setattr(s, field, d[field])
    db.session.commit()
    return jsonify(s.to_dict())


def _resolve_skill_id(skill_id, skill_name_raw):
    """Resolve skill_id either from ID or canonicalized skill_name."""
    if skill_id:
        return skill_id if db.session.get(Skill, skill_id) else None
    if not skill_name_raw:
        return None
    from services.skill_normalizer import canonicalize_skill_name
    sk_name = canonicalize_skill_name(str(skill_name_raw).strip())
    if not sk_name:
        return None
    sk = Skill.query.filter(db.func.lower(Skill.name) == sk_name.lower()).first()
    if not sk:
        sk = Skill(name=sk_name, category="General", source="MANUAL")
        db.session.add(sk)
        db.session.flush()
    return sk.id


# ──────────────────────────────────────────────────────────────────────────────
# Skills
# ──────────────────────────────────────────────────────────────────────────────
@api.post("/students/<int:sid>/skills")
def add_skill(sid):
    """FR-002/FR-003 — Add or update a skill proficiency for a student."""
    if not db.session.get(Student, sid):
        return jsonify({"error": "student not found"}), 404

    d = request.get_json() or {}
    skill_id = _resolve_skill_id(d.get("skill_id"), d.get("skill_name"))
    if not skill_id:
        return jsonify({"error": "skill_id or valid skill_name is required"}), 400

    try:
        prof = float(d.get("proficiency", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "proficiency must be a number"}), 400
    if not 0 <= prof <= 100:
        return jsonify({"error": "proficiency must be between 0 and 100"}), 400

    row = StudentSkill.query.filter_by(student_id=sid, skill_id=skill_id).first()
    if row:
        row.proficiency   = prof
        row.evidence_type = d.get("evidence_type", row.evidence_type)
    else:
        row = StudentSkill(
            student_id=sid, skill_id=skill_id, proficiency=prof,
            evidence_type=d.get("evidence_type", "self_reported"),
        )
        db.session.add(row)
    db.session.commit()
    return jsonify({"id": row.id, "proficiency": prof}), 201


# ──────────────────────────────────────────────────────────────────────────────
# Assessments
# ──────────────────────────────────────────────────────────────────────────────
@api.post("/students/<int:sid>/assessments")
def assessment(sid):
    """FR-009 — Submit assessment result; derives and persists proficiency."""
    d = request.get_json() or {}
    skill_id = _resolve_skill_id(d.get("skill_id"), d.get("skill_name"))
    if not skill_id:
        return jsonify({"error": "skill_id or valid skill_name is required"}), 400

    try:
        score   = float(d.get("score", 0))
        maximum = float(d.get("max_score", 100))
    except (TypeError, ValueError):
        return jsonify({"error": "score and max_score must be numbers"}), 400

    if maximum <= 0 or not 0 <= score <= maximum:
        return jsonify({"error": f"score must be 0–{maximum}"}), 400

    # Determine attempt number
    prev = Assessment.query.filter_by(
        student_id=sid, skill_id=skill_id
    ).count()

    a = Assessment(
        student_id=sid, skill_id=skill_id,
        score=score, max_score=maximum, attempt_no=prev + 1,
    )
    db.session.add(a)

    prof = round(score / maximum * 100, 2)
    row = StudentSkill.query.filter_by(student_id=sid, skill_id=skill_id).first()
    if row:
        row.proficiency   = prof
        row.evidence_type = "assessment"
    else:
        db.session.add(StudentSkill(
            student_id=sid, skill_id=skill_id,
            proficiency=prof, evidence_type="assessment",
        ))
    db.session.commit()
    return jsonify({"assessment_id": a.id, "proficiency": prof, "attempt_no": a.attempt_no}), 201


# ──────────────────────────────────────────────────────────────────────────────
# Projects & Certifications
# ──────────────────────────────────────────────────────────────────────────────
@api.post("/students/<int:sid>/projects")
def add_project(sid):
    """FR-007 — Add a student project."""
    d = request.get_json() or {}
    title = (d.get("title") or "").strip()
    if not title:
        return jsonify({"error": "title is required"}), 400
    p = Project(
        student_id=sid, title=title,
        description=d.get("description"),
        skills_used=d.get("skills_used"),
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"id": p.id, "title": p.title}), 201


@api.post("/students/<int:sid>/certifications")
def add_certification(sid):
    """FR-008 — Add a student certification."""
    d = request.get_json() or {}
    name = (d.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name is required"}), 400
    c = Certification(
        student_id=sid, name=name,
        issuer=d.get("issuer"),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({"id": c.id, "name": c.name}), 201


# ──────────────────────────────────────────────────────────────────────────────
# Resume Upload & Parsing
# ──────────────────────────────────────────────────────────────────────────────
@api.post("/students/<int:sid>/resume")
def upload_resume(sid):
    """FR-010 — Upload and parse a PDF/DOCX resume."""
    if not db.session.get(Student, sid):
        return jsonify({"error": "student not found"}), 404

    f = request.files.get("file") or request.files.get("resume")
    if not f:
        return jsonify({"error": "file is required (form field 'file' or 'resume')"}), 400

    ext = Path(f.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({"error": f"Only PDF and DOCX files are supported. Got: {ext}"}), 400

    upload_dir = Path(current_app.config["UPLOAD_DIR"])
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = secure_filename(f.filename or "resume")
    save_path = upload_dir / f"{sid}_{safe_name}"
    f.save(save_path)

    try:
        text = extract_text(str(save_path))
        extracted = candidate_skills(text)
        projects  = extract_projects_text(text)
        certs     = extract_certifications_text(text)

        r = Resume(
            student_id=sid, file_name=safe_name,
            stored_path=str(save_path), extracted_text=text,
            processing_status="processed",
        )
        db.session.add(r)
        db.session.commit()

        return jsonify({
            "resume_id":         r.id,
            "extracted_skills":  extracted,
            "extracted_projects": projects,
            "extracted_certs":   certs,
            "message": (
                "Review the extracted items and confirm skills "
                "via POST /api/students/{id}/skills"
            ),
        }), 201

    except Exception as exc:
        log.exception("Resume processing failed for student %s", sid)
        return jsonify({"error": f"Resume processing failed: {exc}"}), 422


# ──────────────────────────────────────────────────────────────────────────────
# Roles
# ──────────────────────────────────────────────────────────────────────────────
@api.get("/roles")
def list_roles():
    """List all available target job roles."""
    roles = JobRole.query.order_by(JobRole.name).all()
    return jsonify([r.to_dict() for r in roles])


@api.get("/roles/<int:rid>/skills")
def role_skills(rid):
    """
    Return the required skills for a role with dual-taxonomy breakdown.

    Query params:
        category: 'technical' | 'knowledge' | 'activity' | 'all'  (default: 'all')
            - 'technical'  → ESCO hard skills only
            - 'knowledge'  → O*NET Knowledge competencies only
            - 'activity'   → O*NET Work Activity competencies only
            - 'all'        → All skills (ESCO + O*NET)
    """
    role = db.session.get(JobRole, rid)
    if not role:
        return jsonify({"error": "role not found"}), 404

    category_filter = request.args.get("category", "all").lower()

    rows = (
        db.session.query(JobSkill, Skill)
        .join(Skill, Skill.id == JobSkill.skill_id)
        .filter(JobSkill.job_role_id == rid)
        .all()
    )

    # Apply category filter
    filtered_rows = []
    for js, sk in rows:
        cat = (sk.category or "").lower()
        if category_filter == "technical" and "o*net" in cat:
            continue
        elif category_filter == "knowledge" and cat != "o*net knowledge":
            continue
        elif category_filter == "activity" and cat != "o*net work activity":
            continue
        filtered_rows.append((js, sk))

    # Count by taxonomy
    total_technical = sum(1 for _, sk in rows if "o*net" not in (sk.category or "").lower())
    total_knowledge  = sum(1 for _, sk in rows if (sk.category or "").lower() == "o*net knowledge")
    total_activity   = sum(1 for _, sk in rows if (sk.category or "").lower() == "o*net work activity")

    return jsonify({
        "role": role.to_dict(),
        # Convenience flat fields (backward-compatible)
        "role_id":   role.id,
        "role_name": role.name,
        "onet_code": role.onet_code,
        "esco_uri":  role.source_identifier,
        # Taxonomy breakdown counts
        "technical_skills_count":  total_technical,
        "onet_competencies_count": total_knowledge + total_activity,
        "total_skills":            len(rows),
        "filtered_count":          len(filtered_rows),
        "category_filter":         category_filter,
        # Skills list (filtered)
        "required_skills": [
            {
                "skill_id":       sk.id,
                "skill":          sk.name,
                "category":       sk.category,
                "source":         sk.source,
                "required_level": js.required_level,
                "importance":     js.importance,
                "relation_type":  js.relation_type,
                "source":         js.source,
            }
            for js, sk in filtered_rows
        ],
    })


# ──────────────────────────────────────────────────────────────────────────────
# Skill Gap Analysis
# ──────────────────────────────────────────────────────────────────────────────
@api.post("/skill-gap/analyze")
def gap_analyze():
    """FR-060 — Run gap analysis for a student against a target role."""
    d = request.get_json() or {}
    student_id  = d.get("student_id")
    job_role_id = d.get("job_role_id") or d.get("role_id")
    if not student_id or not job_role_id:
        return jsonify({"error": "student_id and job_role_id (or role_id) are required"}), 400
    if not db.session.get(Student, student_id):
        return jsonify({"error": "student not found"}), 404
    if not db.session.get(JobRole, job_role_id):
        return jsonify({"error": "job role not found"}), 404

    gaps = analyze(int(student_id), int(job_role_id))
    return jsonify({"student_id": student_id, "job_role_id": job_role_id, "gaps": gaps})


@api.get("/students/<int:sid>/gaps")
def get_gaps(sid):
    """Retrieve most recent gap analysis for a student."""
    role_id = request.args.get("job_role_id", type=int) or request.args.get("role_id", type=int)
    query = (
        db.session.query(SkillGap, Skill)
        .join(Skill, Skill.id == SkillGap.skill_id)
        .filter(SkillGap.student_id == sid)
    )
    if role_id:
        query = query.filter(SkillGap.job_role_id == role_id)
    else:
        latest = (
            SkillGap.query
            .filter_by(student_id=sid)
            .order_by(SkillGap.id.desc())
            .first()
        )
        if latest and latest.job_role_id:
            query = query.filter(SkillGap.job_role_id == latest.job_role_id)
    rows = query.order_by(SkillGap.priority_score.desc()).all()
    return jsonify([gap.to_dict(skill_name=skill.name) for gap, skill in rows])


# ──────────────────────────────────────────────────────────────────────────────
# Recommendations
# ──────────────────────────────────────────────────────────────────────────────
@api.get("/students/<int:sid>/recommendations")
def get_recommendations(sid):
    """FR-070 — Return top-K personalized course recommendations."""
    top_k = max(1, min(request.args.get("top_k", 10, type=int), 50))
    role_id = request.args.get("job_role_id", type=int) or request.args.get("role_id", type=int)
    return jsonify(recommend(sid, top_k=top_k, job_role_id=role_id))


# ──────────────────────────────────────────────────────────────────────────────
# Learning Progress
# ──────────────────────────────────────────────────────────────────────────────
@api.post("/students/<int:sid>/progress")
def record_progress(sid):
    """FR-080 — Record a learning progress update."""
    d = request.get_json() or {}
    course_id = d.get("course_id")
    title = (d.get("title") or "").strip()
    if not title and course_id:
        c = db.session.get(Course, course_id)
        if c:
            title = c.title
    if not title:
        title = f"Course #{course_id}" if course_id else "Learning Module"

    try:
        completion = float(d.get("completion") if d.get("completion") is not None else d.get("completion_pct", 0))
    except (TypeError, ValueError):
        return jsonify({"error": "completion must be a number"}), 400
    if not 0 <= completion <= 100:
        return jsonify({"error": "completion must be between 0 and 100"}), 400

    status = (d.get("status") or "").lower().strip()
    valid_statuses = ("not_started", "in_progress", "completed")
    if d.get("status") is not None and status not in valid_statuses:
        return jsonify({"error": f"status must be one of: {', '.join(valid_statuses)}"}), 400
    if not status:
        # Auto-derive status from completion if not provided
        status = "completed" if completion >= 100 else ("in_progress" if completion > 0 else "not_started")

    p = LearningProgress(
        student_id=sid,
        course_id=course_id,
        skill_id=d.get("skill_id"),
        title=title, status=status, completion=completion,
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"id": p.id, "status": status, "completion": completion}), 201


# ──────────────────────────────────────────────────────────────────────────────
# Reassessment
# ──────────────────────────────────────────────────────────────────────────────
@api.post("/students/<int:sid>/reassessment")
def reassessment(sid):
    """
    FR-083 — Submit reassessment.
    Updates StudentSkill, persists Reassessment, and re-runs gap analysis if
    job_role_id is supplied.
    """
    d = request.get_json() or {}
    skill_id = _resolve_skill_id(d.get("skill_id"), d.get("skill_name"))
    if not skill_id:
        return jsonify({"error": "skill_id or valid skill_name is required"}), 400

    try:
        if "new_level" in d:
            new_level = float(d["new_level"])
        elif "score" in d and "max_score" in d:
            new_level = round(float(d["score"]) / float(d["max_score"]) * 100, 2)
        else:
            new_level = float(d.get("new_level", 0))
    except (TypeError, ValueError, ZeroDivisionError):
        return jsonify({"error": "new_level or score/max_score must be numbers"}), 400
    if not 0 <= new_level <= 100:
        return jsonify({"error": "new_level must be between 0 and 100"}), 400

    row = StudentSkill.query.filter_by(student_id=sid, skill_id=skill_id).first()
    old_level = float(row.proficiency) if row else 0.0

    if row:
        row.proficiency   = new_level
        row.evidence_type = "reassessment"
    else:
        db.session.add(StudentSkill(
            student_id=sid, skill_id=skill_id,
            proficiency=new_level, evidence_type="reassessment",
        ))

    r = Reassessment(
        student_id=sid, skill_id=skill_id,
        old_level=old_level, new_level=new_level,
        improvement=round(new_level - old_level, 2),
    )
    db.session.add(r)
    db.session.commit()

    result = {
        "old_level":   old_level,
        "new_level":   new_level,
        "improvement": r.improvement,
    }

    # Optionally refresh gap analysis if a role is supplied
    job_role_id = d.get("job_role_id")
    if job_role_id and db.session.get(JobRole, job_role_id):
        updated_gaps = analyze(sid, int(job_role_id))
        result["updated_gaps"] = updated_gaps

    return jsonify(result), 201


# ──────────────────────────────────────────────────────────────────────────────
# Dashboard
# ──────────────────────────────────────────────────────────────────────────────
@api.get("/students/<int:sid>/dashboard")
def dashboard(sid):
    """
    FR-084 — Aggregated student dashboard.
    Returns: profile, current skills radar data, top gaps, active learning path,
             progress summary, and reassessment history.
    """
    s = db.session.get(Student, sid)
    if not s:
        return jsonify({"error": "student not found"}), 404

    # Current skills
    skill_rows = (
        db.session.query(StudentSkill, Skill)
        .join(Skill, Skill.id == StudentSkill.skill_id)
        .filter(StudentSkill.student_id == sid)
        .all()
    )

    # Top 5 priority gaps (across all roles)
    top_gaps = (
        db.session.query(SkillGap, Skill, JobRole)
        .join(Skill,   Skill.id   == SkillGap.skill_id)
        .join(JobRole, JobRole.id == SkillGap.job_role_id)
        .filter(SkillGap.student_id == sid, SkillGap.gap_value > 0)
        .order_by(SkillGap.priority_score.desc())
        .limit(5)
        .all()
    )

    # Active recommendations (not_started or in_progress)
    active_progress = (
        LearningProgress.query
        .filter(LearningProgress.student_id == sid,
                LearningProgress.status != "completed")
        .order_by(LearningProgress.updated_at.desc())
        .limit(10)
        .all()
    )

    # Completed courses
    completed = (
        LearningProgress.query
        .filter(LearningProgress.student_id == sid,
                LearningProgress.status == "completed")
        .count()
    )

    # Reassessment history
    history = (
        db.session.query(Reassessment, Skill)
        .join(Skill, Skill.id == Reassessment.skill_id)
        .filter(Reassessment.student_id == sid)
        .order_by(Reassessment.assessed_at.desc())
        .limit(10)
        .all()
    )

    # Top recommendations
    top_recs = (
        db.session.query(Recommendation, Skill, Course)
        .join(Skill,  Skill.id  == Recommendation.skill_id)
        .join(Course, Course.id == Recommendation.course_id)
        .filter(Recommendation.student_id == sid)
        .order_by(Recommendation.score.desc())
        .limit(5)
        .all()
    )

    return jsonify({
        "student": s.to_dict(),
        "current_skills": [
            {
                "skill": sk.name, "category": sk.category,
                "proficiency": ss.proficiency, "evidence_type": ss.evidence_type,
            }
            for ss, sk in skill_rows
        ],
        "top_gaps": [
            {
                "role":          role.name,
                "skill":         skill.name,
                "current_level": gap.current_level,
                "required_level": gap.required_level,
                "severity":      gap.severity,
                "priority_score": gap.priority_score,
            }
            for gap, skill, role in top_gaps
        ],
        "active_learning_path": [
            {
                "title":      lp.title,
                "status":     lp.status,
                "completion": lp.completion,
            }
            for lp in active_progress
        ],
        "progress_summary": {
            "completed_courses": completed,
            "in_progress":       sum(1 for lp in active_progress if lp.status == "in_progress"),
            "not_started":       sum(1 for lp in active_progress if lp.status == "not_started"),
        },
        "top_recommendations": [
            {
                "skill":    skill.name,
                "course":   course.title,
                "provider": course.provider,
                "score":    rec.score,
                "reason":   rec.reason,
                "url":      course.url,
            }
            for rec, skill, course in top_recs
        ],
        "reassessment_history": [
            {
                "skill":       skill.name,
                "old_level":   ra.old_level,
                "new_level":   ra.new_level,
                "improvement": ra.improvement,
                "date":        ra.assessed_at.isoformat() if ra.assessed_at else None,
            }
            for ra, skill in history
        ],
    })


# ──────────────────────────────────────────────────────────────────────────────
# 📊 Job Role Match Score
# ──────────────────────────────────────────────────────────────────────────────
@api.get("/students/<int:sid>/role-match")
def role_match(sid):
    """
    Compute how well a student matches each job role.

    Optional query param:
        ?job_role_id=<int>  — limit to one specific role

    Returns a list sorted by match_score descending.
    Each entry includes:
        match_score     (0–100),  ready (bool),
        by_category     (per-skill-category percentages),
        top_missing     (top 5 skills not yet acquired),
        verdict         (human-readable label)
    """
    s = db.session.get(Student, sid)
    if not s:
        return jsonify({"error": "student not found"}), 404

    job_role_id = request.args.get("job_role_id", type=int)

    # Check cache
    cached = _cache.get_match(sid)
    if cached is not None and not job_role_id:
        return jsonify({"matches": cached, "cached": True})

    matches = compute_role_match(sid, job_role_id)

    if not job_role_id:          # Only cache the all-roles result
        _cache.set_match(sid, matches)

    return jsonify({"student_id": sid, "matches": matches})


# ──────────────────────────────────────────────────────────────────────────────
# 🗺️ Personalized Learning Path
# ──────────────────────────────────────────────────────────────────────────────
@api.post("/students/<int:sid>/learning-path")
def create_learning_path(sid):
    """
    Generate (or regenerate) a personalized learning path.

    Required query param:
        ?job_role_id=<int>

    The path is grouped into phases by gap severity:
        Phase 1 — HIGH severity (critical gaps)
        Phase 2 — MEDIUM severity (core gaps)
        Phase 3 — LOW severity (polish)

    Requires gap analysis to have been run first.
    """
    s = db.session.get(Student, sid)
    if not s:
        return jsonify({"error": "student not found"}), 404

    job_role_id = request.args.get("job_role_id", type=int)
    if not job_role_id:
        return jsonify({"error": "job_role_id query param is required"}), 400

    if not db.session.get(JobRole, job_role_id):
        return jsonify({"error": "job role not found"}), 404

    result = generate_learning_path(sid, job_role_id)
    if "error" in result:
        return jsonify(result), 400

    # Invalidate match cache (path generation changes context)
    _cache.invalidate_student(sid)

    return jsonify(result), 201


@api.get("/students/<int:sid>/learning-path")
def get_student_learning_path(sid):
    """
    Retrieve the most recently generated learning path for a student.

    Required query param:
        ?job_role_id=<int>
    """
    s = db.session.get(Student, sid)
    if not s:
        return jsonify({"error": "student not found"}), 404

    job_role_id = request.args.get("job_role_id", type=int)
    if not job_role_id:
        return jsonify({"error": "job_role_id query param is required"}), 400

    # Check cache
    cached = _cache.get_path(sid, job_role_id)
    if cached is not None:
        return jsonify({**cached, "cached": True})

    path = get_learning_path(sid, job_role_id)
    if not path:
        return jsonify({
            "message": "No learning path found. Run POST /students/<id>/learning-path first."
        }), 404

    _cache.set_path(sid, job_role_id, path)
    return jsonify(path)


# ──────────────────────────────────────────────────────────────────────────────
# 📈 Skill Progress Analytics
# ──────────────────────────────────────────────────────────────────────────────
@api.get("/students/<int:sid>/analytics")
def student_analytics(sid):
    """
    Skill progress analytics for a student.

    Returns:
        summary:              total skills, avg proficiency, reassessment stats
        top_improved_skills:  top 5 most-improved skills with gain amounts
        regressed_skills:     skills that went down (regression detection)
        skill_trends:         time-series {skill_name: [{date, level}]}
        assessment_history:   all assessment scores with dates
        gap_severity_counts:  {HIGH: N, MEDIUM: N, LOW: N}
        best_fit_role:        role with fewest HIGH severity gaps
    """
    s = db.session.get(Student, sid)
    if not s:
        return jsonify({"error": "student not found"}), 404

    analytics = compute_analytics(sid)
    return jsonify({"student_id": sid, **analytics})


# ──────────────────────────────────────────────────────────────────────────────
# ⚡ Cache Statistics (debug)
# ──────────────────────────────────────────────────────────────────────────────
@api.get("/cache/stats")
def cache_stats():
    """Return current in-memory cache sizes and TTLs. Useful for debugging."""
    return jsonify(_cache.cache_stats())
