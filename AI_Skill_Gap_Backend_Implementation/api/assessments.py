"""
api/assessments.py — Assessment and reassessment API blueprint.
"""
from flask import Blueprint, request
from schemas import validate_json
from schemas.assessment_schemas import AssessmentSubmitSchema, ReassessmentSubmitSchema
from services.assessment_service import AssessmentService
from auth import require_student_auth

assessments_bp = Blueprint("assessments_v1", __name__)


@assessments_bp.post("/students/<int:sid>/assessments")
@validate_json(AssessmentSubmitSchema)
def submit_assessment(sid, validated_data):
    """Submit assessment result; derives and persists proficiency."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    result, err_msg, status_code = AssessmentService.submit_assessment(sid, validated_data)
    if err_msg:
        return api_response(message=err_msg, status_code=status_code)
    return api_response(data=result, status_code=status_code)


@assessments_bp.post("/students/<int:sid>/reassessment")
@validate_json(ReassessmentSubmitSchema)
def submit_reassessment(sid, validated_data):
    """Submit reassessment, update student skills, and recalculate gaps."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    result, err_msg, status_code = AssessmentService.submit_reassessment(sid, validated_data)
    if err_msg:
        return api_response(message=err_msg, status_code=status_code)
    return api_response(data=result, status_code=status_code)
