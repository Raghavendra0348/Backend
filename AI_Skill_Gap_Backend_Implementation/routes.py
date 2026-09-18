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
from services.analytics import AnalyticsService, compute_analytics
from services.student_service import StudentService
from services.role_service import RoleService
from services.skill_service import SkillService
from services.assessment_service import AssessmentService
from services.resume_service import ResumeService
from auth import require_student_auth, get_student_id_from_jwt

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
    limit    = request.args.get("limit", 100, type=int)
    if limit is None or limit < 1:
        limit = 100
    limit = min(limit, 500)

    result = SkillService.list_skills(search=search, category=category, limit=limit)
    return jsonify(result)


# ──────────────────────────────────────────────────────────────────────────────
# Students
# ──────────────────────────────────────────────────────────────────────────────
@api.post("/students")
def create_student():
    """FR-001 — Create a student profile."""
    d = request.get_json() or {}
    s, err, status_code = StudentService.create_student(d)
    if err:
        return jsonify({"error": err}), status_code
    return jsonify({"id": s.id, "name": s.name}), 201


@api.get("/students")
def list_students():
    """List recent students (up to limit, default 50)."""
    limit = request.args.get("limit", 50, type=int)
    if limit is None or limit < 1:
        limit = 50
    limit = min(limit, 100)
    students = StudentService.list_students(limit=limit)
    return jsonify(students)


@api.get("/students/<int:sid>")
def get_student(sid):
    """Get student profile with current skills."""
    student, err = require_student_auth(sid)
    if err:
        return err

    profile = StudentService.get_student_profile(sid)
    if not profile:
        return jsonify({"error": "student not found"}), 404
    return jsonify(profile)


@api.put("/students/<int:sid>")
def update_student(sid):
    """Update student profile fields."""
    student, err = require_student_auth(sid)
    if err:
        return err
    d = request.get_json() or {}
    s = StudentService.update_student(sid, d)
    if not s:
        return jsonify({"error": "student not found"}), 404
    return jsonify(s.to_dict())


def _resolve_skill_id(skill_id, skill_name_raw):
    """Resolve skill_id either from ID or canonicalized skill_name."""
    return SkillService.resolve_skill_id(skill_id, skill_name_raw)


# ──────────────────────────────────────────────────────────────────────────────
# Skills
# ──────────────────────────────────────────────────────────────────────────────
@api.post("/students/<int:sid>/skills")
def add_skill(sid):
    """FR-002/FR-003 — Add or update a skill proficiency for a student."""
    _, err = require_student_auth(sid)
    if err:
        return err

    d = request.get_json() or {}
    res, err_msg, status_code = StudentService.add_or_update_skill(
        student_id=sid,
        skill_id=d.get("skill_id"),
        skill_name=d.get("skill_name"),
        proficiency=d.get("proficiency", 0),
        evidence_type=d.get("evidence_type", "self_reported"),
    )
    if err_msg:
        return jsonify({"error": err_msg}), status_code

    row = StudentSkill.query.filter_by(student_id=sid, skill_id=res["skill_id"]).first()
    row_id = row.id if row else res.get("id", res["skill_id"])
    return jsonify({"id": row_id, "proficiency": res["proficiency"]}), 201


# ──────────────────────────────────────────────────────────────────────────────
# Assessments
# ──────────────────────────────────────────────────────────────────────────────
@api.post("/students/<int:sid>/assessments")
def assessment(sid):
    """FR-009 — Submit assessment result; derives and persists proficiency."""
    _, err = require_student_auth(sid)
    if err:
        return err
    d = request.get_json() or {}
    result, err_msg, status_code = AssessmentService.submit_assessment(sid, d)
    if err_msg:
        return jsonify({"error": err_msg}), status_code
    return jsonify(result), 201


# ──────────────────────────────────────────────────────────────────────────────
# Projects & Certifications
# ──────────────────────────────────────────────────────────────────────────────
@api.post("/students/<int:sid>/projects")
def add_project(sid):
    """FR-007 — Add a student project."""
    _, err = require_student_auth(sid)
    if err:
        return err
    d = request.get_json() or {}
    result, err_msg, status_code = ResumeService.add_project(sid, d)
    if err_msg:
        return jsonify({"error": err_msg}), status_code
    return jsonify(result), 201


@api.post("/students/<int:sid>/certifications")
def add_certification(sid):
    """FR-008 — Add a student certification."""
    _, err = require_student_auth(sid)
    if err:
        return err
    d = request.get_json() or {}
    result, err_msg, status_code = ResumeService.add_certification(sid, d)
    if err_msg:
        return jsonify({"error": err_msg}), status_code
    return jsonify(result), 201


# ──────────────────────────────────────────────────────────────────────────────
# Resume Upload & Parsing
# ──────────────────────────────────────────────────────────────────────────────
@api.post("/students/<int:sid>/resume")
def upload_resume(sid):
    """FR-010 — Upload and parse a PDF/DOCX resume."""
    _, err = require_student_auth(sid)
    if err:
        return err

    f = request.files.get("file") or request.files.get("resume")
    if not f:
        return jsonify({"error": "file is required (form field 'file' or 'resume')"}), 400

    upload_dir = current_app.config.get("UPLOAD_DIR", "storage/uploads")
    result, err_msg, status_code = ResumeService.process_resume(sid, f, upload_dir)
    if err_msg:
        return jsonify({"error": err_msg}), status_code

    return jsonify({
        "resume_id":         result["resume_id"],
        "extracted_skills":  result["extracted_skills"],
        "extracted_projects": result["extracted_projects"],
        "extracted_certs":   result["extracted_certs"],
        "message": (
            "Review the extracted items and confirm skills "
            "via POST /api/students/{id}/skills"
        ),
    }), 201


# ──────────────────────────────────────────────────────────────────────────────
# Roles
# ──────────────────────────────────────────────────────────────────────────────
@api.get("/roles")
def list_roles():
    """List all available target job roles."""
    return jsonify(RoleService.list_roles())


@api.get("/roles/<int:rid>/skills")
def role_skills(rid):
    """
    Return the required skills for a role with dual-taxonomy breakdown.

    Query params:
        category: 'technical' | 'knowledge' | 'activity' | 'all'  (default: 'all')
    """
    category_filter = request.args.get("category", "all")
    result, err_msg, status_code = RoleService.get_role_skills(rid, category_filter=category_filter)
    if err_msg:
        return jsonify({"error": err_msg}), status_code
    return jsonify(result)


# ──────────────────────────────────────────────────────────────────────────────
# Skill Gap Analysis
# ──────────────────────────────────────────────────────────────────────────────
@api.post("/skill-gap/analyze")
def gap_analyze():
    """FR-060 — Run gap analysis for a student against a target role.

    student_id is derived from the JWT token (if present).
    Falls back to body student_id for unauthenticated/legacy calls.
    """
    d = request.get_json() or {}
    job_role_id = d.get("job_role_id") or d.get("role_id")
    if not job_role_id:
        return jsonify({"error": "job_role_id (or role_id) is required"}), 400

    # Prefer JWT-derived student_id; fall back to body for unauthenticated calls
    student_id = get_student_id_from_jwt() or d.get("student_id")
    if not student_id:
        return jsonify({"error": "student_id is required (send JWT token or include in body)"}), 400

    if not db.session.get(Student, student_id):
        return jsonify({"error": "student not found"}), 404
    if not db.session.get(JobRole, job_role_id):
        return jsonify({"error": "job role not found"}), 404

    gaps = analyze(int(student_id), int(job_role_id))
    return jsonify({"student_id": student_id, "job_role_id": job_role_id, "gaps": gaps})


@api.get("/students/<int:sid>/gaps")
def get_gaps(sid):
    """Retrieve most recent gap analysis for a student."""
    _, err = require_student_auth(sid)
    if err:
        return err
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
    _, err = require_student_auth(sid)
    if err:
        return err
    top_k = max(1, min(request.args.get("top_k", 10, type=int), 50))
    role_id = request.args.get("job_role_id", type=int) or request.args.get("role_id", type=int)
    return jsonify(recommend(sid, top_k=top_k, job_role_id=role_id))


# ──────────────────────────────────────────────────────────────────────────────
# Learning Progress
# ──────────────────────────────────────────────────────────────────────────────
@api.post("/students/<int:sid>/progress")
def record_progress(sid):
    """FR-080 — Record a learning progress update."""
    _, err = require_student_auth(sid)
    if err:
        return err
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
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    _cache.invalidate_student(sid)
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
    _, err = require_student_auth(sid)
    if err:
        return err
    d = request.get_json() or {}
    result, err_msg, status_code = AssessmentService.submit_reassessment(sid, d)
    if err_msg:
        return jsonify({"error": err_msg}), status_code
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
    student, err = require_student_auth(sid)
    if err:
        return err

    data = AnalyticsService.get_dashboard(sid)
    if not data:
        return jsonify({"error": "student not found"}), 404
    return jsonify(data)


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
    student, err = require_student_auth(sid)
    if err:
        return err
    s = student

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
    _, err = require_student_auth(sid)
    if err:
        return err

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
    _, err = require_student_auth(sid)
    if err:
        return err

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
    _, err = require_student_auth(sid)
    if err:
        return err

    analytics = compute_analytics(sid)
    return jsonify({"student_id": sid, **analytics})


# ──────────────────────────────────────────────────────────────────────────────
# ⚡ Cache Statistics (debug)
# ──────────────────────────────────────────────────────────────────────────────
@api.get("/cache/stats")
def cache_stats():
    """Return current in-memory cache sizes and TTLs. Useful for debugging."""
    return jsonify(_cache.cache_stats())
