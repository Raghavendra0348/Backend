"""
api/__init__.py — Modular API blueprint aggregation and standard response envelope.
"""
from flask import Blueprint, jsonify

api_v1 = Blueprint("api_v1", __name__)


def api_response(data=None, message=None, meta=None, status_code=200):
    """
    Standardized API response envelope:
    {
        "success": bool,
        "message": optional str,
        "data": optional payload (dict/list),
        "meta": optional metadata dict
    }
    """
    payload = {"success": 200 <= status_code < 300}
    if message is not None:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    if meta is not None:
        payload["meta"] = meta
    return jsonify(payload), status_code


# Import sub-blueprints and register them to api_v1
from api.students import students_bp
from api.skills import skills_bp
from api.roles import roles_bp
from api.assessments import assessments_bp
from api.resumes import resumes_bp
from api.gap_analysis import gap_bp
from api.recommendations import recommendations_bp
from api.learning import learning_bp
from api.analytics import analytics_bp

api_v1.register_blueprint(students_bp)
api_v1.register_blueprint(skills_bp)
api_v1.register_blueprint(roles_bp)
api_v1.register_blueprint(assessments_bp)
api_v1.register_blueprint(resumes_bp)
api_v1.register_blueprint(gap_bp)
api_v1.register_blueprint(recommendations_bp)
api_v1.register_blueprint(learning_bp)
api_v1.register_blueprint(analytics_bp)
