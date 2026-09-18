"""
api/gap_analysis.py — Skill gap analysis and role match API blueprint.
"""
from flask import Blueprint, request
from extensions import db
from models import Student, JobRole, SkillGap, Skill
from schemas import validate_json
from schemas.gap_schemas import GapAnalyzeSchema
from services.gap_engine import analyze
from services.role_matcher import compute_role_match
from auth import require_student_auth, get_student_id_from_jwt
import cache as _cache

gap_bp = Blueprint("gap_v1", __name__)


@gap_bp.post("/skill-gap/analyze")
@validate_json(GapAnalyzeSchema)
def gap_analyze(validated_data):
    """FR-060 — Run gap analysis for a student against a target role."""
    from api import api_response
    job_role_id = validated_data.get("job_role_id") or validated_data.get("role_id")
    student_id = get_student_id_from_jwt() or validated_data.get("student_id")

    if not student_id:
        return api_response(
            message="student_id is required (send JWT token or include in body)",
            status_code=400
        )

    if not db.session.get(Student, student_id):
        return api_response(message="student not found", status_code=404)
    if not db.session.get(JobRole, job_role_id):
        return api_response(message="job role not found", status_code=404)

    gaps = analyze(int(student_id), int(job_role_id))
    return api_response(data={
        "student_id": int(student_id),
        "job_role_id": int(job_role_id),
        "gaps": gaps
    })


@gap_bp.get("/students/<int:sid>/gaps")
def get_gaps(sid):
    """Retrieve most recent persisted gap analysis for a student."""
    from api import api_response
    student, err = require_student_auth(sid)
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
        if latest:
            query = query.filter(SkillGap.job_role_id == latest.job_role_id)

    rows = query.order_by(SkillGap.priority_score.desc()).all()
    result = [
        {
            **gap.to_dict(skill_name=skill.name),
            "id": gap.id,
            "category": skill.category,
            "created_at": gap.created_at.isoformat() if gap.created_at else None,
        }
        for gap, skill in rows
    ]
    return api_response(data=result)


@gap_bp.get("/students/<int:sid>/role-match")
def role_match(sid):
    """Compute how well a student matches job roles."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    job_role_id = request.args.get("job_role_id", type=int)

    cached = _cache.get_match(sid)
    if cached is not None and not job_role_id:
        return api_response(data={"matches": cached, "cached": True})

    matches = compute_role_match(sid, job_role_id)
    if not job_role_id:
        _cache.set_match(sid, matches)

    return api_response(data={"student_id": sid, "matches": matches})
