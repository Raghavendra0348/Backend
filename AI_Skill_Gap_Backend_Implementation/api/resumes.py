"""
api/resumes.py — Resume parsing, projects, and certifications API blueprint.
"""
from flask import Blueprint, request, current_app
from schemas import validate_json
from schemas.resume_schemas import ProjectCreateSchema, CertificationCreateSchema
from services.resume_service import ResumeService
from auth import require_student_auth
import pathlib
import tempfile

resumes_bp = Blueprint("resumes_v1", __name__)


@resumes_bp.post("/students/<int:sid>/projects")
@validate_json(ProjectCreateSchema)
def add_project(sid, validated_data):
    """Add a student project."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    result, err_msg, status_code = ResumeService.add_project(sid, validated_data)
    if err_msg:
        return api_response(message=err_msg, status_code=status_code)
    return api_response(data=result, status_code=status_code)


@resumes_bp.post("/students/<int:sid>/certifications")
@validate_json(CertificationCreateSchema)
def add_certification(sid, validated_data):
    """Add a student certification."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    result, err_msg, status_code = ResumeService.add_certification(sid, validated_data)
    if err_msg:
        return api_response(message=err_msg, status_code=status_code)
    return api_response(data=result, status_code=status_code)


@resumes_bp.post("/students/<int:sid>/resume")
def upload_resume(sid):
    """Upload and parse a PDF/DOCX resume."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    file_obj = request.files.get("file") or request.files.get("resume")
    # Use the configured upload dir; fall back to the OS temp dir if somehow
    # UPLOAD_DIR is missing from config (cross-platform: %TEMP% on Windows,
    # /tmp on Linux/macOS).
    _default_upload = str(pathlib.Path(tempfile.gettempdir()) / "skill_gap_uploads")
    upload_dir = current_app.config.get("UPLOAD_DIR") or _default_upload

    result, err_msg, status_code = ResumeService.process_resume(sid, file_obj, upload_dir)
    if err_msg:
        return api_response(message=err_msg, status_code=status_code)
    return api_response(data=result, status_code=status_code)


@resumes_bp.get("/students/<int:sid>/resume/evidence")
def get_resume_evidence(sid):
    """Retrieve granular skill evidence records extracted from student resume/projects."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    status_filter = request.args.get("status")
    result, err_msg, status_code = ResumeService.get_extracted_evidence(sid, status_filter)
    if err_msg:
        return api_response(message=err_msg, status_code=status_code)
    return api_response(data=result, status_code=status_code)


@resumes_bp.post("/students/<int:sid>/resume/verify")
def verify_resume_skills(sid):
    """Confirm (accept) or reject AI-extracted skills from resume evidence."""
    from api import api_response
    from schemas.resume_schemas import SkillVerificationListSchema
    student, err = require_student_auth(sid)
    if err:
        return err

    schema = SkillVerificationListSchema()
    try:
        validated_data = schema.load(request.get_json() or {})
    except Exception as exc:
        if hasattr(exc, "messages"):
            return api_response(message="Validation failed", data={"errors": exc.messages}, status_code=400)
        return api_response(message=str(exc), status_code=400)

    result, err_msg, status_code = ResumeService.verify_extracted_skills(
        sid, validated_data.get("verifications", [])
    )
    if err_msg:
        return api_response(message=err_msg, status_code=status_code)
    return api_response(data=result, status_code=status_code)


@resumes_bp.get("/students/<int:sid>/resume/unknown-skills")
def get_unknown_skills(sid):
    """Retrieve unmapped candidate terms pending review in the review queue."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    result, err_msg, status_code = ResumeService.get_unknown_skills(sid)
    if err_msg:
        return api_response(message=err_msg, status_code=status_code)
    return api_response(data=result, status_code=status_code)


@resumes_bp.get("/students/<int:sid>/resume/audits")
def get_extraction_audits(sid):
    """Retrieve AI extraction performance and audit history."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    result, err_msg, status_code = ResumeService.get_extraction_records(sid)
    if err_msg:
        return api_response(message=err_msg, status_code=status_code)
    return api_response(data=result, status_code=status_code)

