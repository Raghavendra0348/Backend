"""
api/skills.py — Skills catalogue API blueprint.
"""
from flask import Blueprint, request
from services.skill_service import SkillService

skills_bp = Blueprint("skills_v1", __name__)


@skills_bp.get("/skills")
def list_skills():
    """
    List all canonical skills.
    Query params:
        search: case-insensitive name substring
        category: exact category filter
        limit: max results (default 100, max 500)
    """
    from api import api_response
    search = (request.args.get("search") or "").strip()
    category = (request.args.get("category") or "").strip()
    limit = request.args.get("limit", 100, type=int)
    if limit is None or limit < 1:
        limit = 100

    result = SkillService.list_skills(search=search, category=category, limit=limit)
    return api_response(data=result)
