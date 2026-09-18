"""
api/learning.py — Learning path generation, retrieval, and progress tracking API blueprint.
"""
from flask import Blueprint, request
from extensions import db
from models import JobRole, Course, LearningProgress
from services.learning_path import generate_learning_path, get_learning_path
from auth import require_student_auth
import cache as _cache

learning_bp = Blueprint("learning_v1", __name__)
VALID_PROGRESS_STATUSES = ("not_started", "in_progress", "completed")


@learning_bp.post("/students/<int:sid>/learning-path")
def create_learning_path(sid):
    """Generate (or regenerate) a personalized learning path."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    # Support query param or json body for job_role_id
    body = request.get_json(silent=True) or {}
    job_role_id = request.args.get("job_role_id", type=int) or body.get("job_role_id")
    if not job_role_id:
        return api_response(message="job_role_id query param or body field is required", status_code=400)

    if not db.session.get(JobRole, job_role_id):
        return api_response(message="job role not found", status_code=404)

    result = generate_learning_path(sid, job_role_id)
    if "error" in result:
        return api_response(message=result["error"], status_code=400)

    _cache.invalidate_student(sid)
    return api_response(data=result, status_code=201)


@learning_bp.get("/students/<int:sid>/learning-path")
def get_student_learning_path(sid):
    """Retrieve the most recently generated learning path for a student."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    job_role_id = request.args.get("job_role_id", type=int)
    if not job_role_id:
        return api_response(message="job_role_id query param is required", status_code=400)

    cached = _cache.get_path(sid, job_role_id)
    if cached is not None:
        return api_response(data={**cached, "cached": True})

    path = get_learning_path(sid, job_role_id)
    if not path:
        return api_response(
            message="No learning path found. Run POST /students/<id>/learning-path first.",
            status_code=404
        )

    _cache.set_path(sid, job_role_id, path)
    return api_response(data=path)


@learning_bp.post("/students/<int:sid>/progress")
def record_progress(sid):
    """Record a learning progress update."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    d = request.get_json(silent=True) or {}
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
        return api_response(message="completion must be a number", status_code=400)

    if not 0 <= completion <= 100:
        return api_response(message="completion must be between 0 and 100", status_code=400)

    status = (d.get("status") or "").lower().strip()
    if d.get("status") is not None and status not in VALID_PROGRESS_STATUSES:
        return api_response(message=f"status must be one of: {', '.join(VALID_PROGRESS_STATUSES)}", status_code=400)
    if not status:
        status = "completed" if completion >= 100 else ("in_progress" if completion > 0 else "not_started")

    p = LearningProgress(
        student_id=sid,
        course_id=course_id,
        skill_id=d.get("skill_id"),
        title=title,
        status=status,
        completion=completion,
    )
    db.session.add(p)
    db.session.commit()

    return api_response(data={"id": p.id, "status": status, "completion": completion}, status_code=201)
