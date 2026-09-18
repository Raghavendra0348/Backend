"""
api/students.py — Student profile and skills API blueprint.
"""
from flask import Blueprint, request
from schemas import validate_json
from schemas.student_schemas import StudentCreateSchema, StudentUpdateSchema, SkillAddSchema
from services.student_service import StudentService
from services.analytics import AnalyticsService
from auth import require_student_auth

students_bp = Blueprint("students_v1", __name__)


@students_bp.post("/students")
@validate_json(StudentCreateSchema)
def create_student(validated_data):
    """Create a new student profile."""
    from api import api_response
    student, err, status_code = StudentService.create_student(validated_data)
    if err:
        return api_response(message=err, status_code=status_code)
    return api_response(data={"id": student.id, "name": student.name}, status_code=201)


@students_bp.get("/students")
def list_students():
    """List recent students."""
    from api import api_response
    limit = request.args.get("limit", 50, type=int)
    if limit is None or limit < 1:
        limit = 50
    students = StudentService.list_students(limit=limit)
    return api_response(data=students)


@students_bp.get("/students/<int:sid>")
def get_student(sid):
    """Get student profile and skills."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    profile = StudentService.get_student_profile(sid)
    if not profile:
        return api_response(message="student not found", status_code=404)
    return api_response(data=profile)


@students_bp.put("/students/<int:sid>")
@validate_json(StudentUpdateSchema)
def update_student(sid, validated_data):
    """Update student profile fields."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    updated = StudentService.update_student(sid, validated_data)
    if not updated:
        return api_response(message="student not found", status_code=404)
    return api_response(data=updated.to_dict())


@students_bp.post("/students/<int:sid>/skills")
@validate_json(SkillAddSchema)
def add_skill(sid, validated_data):
    """Add or update proficiency for a student's skill."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    res, err_msg, status_code = StudentService.add_or_update_skill(
        student_id=sid,
        skill_id=validated_data.get("skill_id"),
        skill_name=validated_data.get("skill_name"),
        proficiency=validated_data.get("proficiency", 0.0),
        evidence_type=validated_data.get("source", "self_reported")
    )
    if err_msg:
        return api_response(message=err_msg, status_code=status_code)
    return api_response(data=res, status_code=status_code)


@students_bp.get("/students/<int:sid>/dashboard")
def get_dashboard(sid):
    """Retrieve full student dashboard summary."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    dashboard_data = AnalyticsService.get_dashboard(sid)
    if not dashboard_data:
        return api_response(message="student not found", status_code=404)
    return api_response(data=dashboard_data)
