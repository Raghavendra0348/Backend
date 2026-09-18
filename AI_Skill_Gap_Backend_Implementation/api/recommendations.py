import json
from flask import Blueprint, request
from services.recommender import recommend, get_recommendation_runs
from auth import require_student_auth

recommendations_bp = Blueprint("recommendations_v1", __name__)


@recommendations_bp.get("/students/<int:sid>/recommendations")
def get_recommendations(sid):
    """FR-070 — Return top-K learning recommendations for a student."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    top_k = request.args.get("top_k", 10, type=int)
    if top_k is None or top_k < 1:
        top_k = 10
    top_k = min(top_k, 50)
    role_id = request.args.get("job_role_id", type=int) or request.args.get("role_id", type=int)

    weights = None
    weights_param = request.args.get("weights")
    if weights_param:
        try:
            weights = json.loads(weights_param)
        except Exception:
            weights = None

    recs = recommend(sid, top_k=top_k, job_role_id=role_id, weights=weights)
    return api_response(data=recs)


@recommendations_bp.get("/students/<int:sid>/recommendations/runs")
def get_recommendation_history(sid):
    """Retrieve historical recommendation run snapshots for a student."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    limit = request.args.get("limit", 10, type=int)
    if limit is None or limit < 1:
        limit = 10
    limit = min(limit, 50)
    runs = get_recommendation_runs(sid, limit=limit)
    return api_response(data=runs)

