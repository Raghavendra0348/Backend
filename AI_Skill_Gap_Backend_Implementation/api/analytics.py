"""
api/analytics.py — Skill progress analytics, system health, and cache stats API blueprint.
"""
from flask import Blueprint
from services.analytics import compute_analytics
from auth import require_student_auth
import cache as _cache

analytics_bp = Blueprint("analytics_v1", __name__)


@analytics_bp.get("/health")
def health():
    """System health check endpoint."""
    from api import api_response
    return api_response(data={"status": "ok"})


@analytics_bp.get("/cache/stats")
def cache_stats():
    """Return in-memory cache metrics."""
    from api import api_response
    return api_response(data=_cache.cache_stats())


@analytics_bp.get("/students/<int:sid>/analytics")
def student_analytics(sid):
    """Skill progress analytics for a student."""
    from api import api_response
    student, err = require_student_auth(sid)
    if err:
        return err

    analytics = compute_analytics(sid)
    return api_response(data={"student_id": sid, **analytics})
