"""
api/roles.py — Job roles and required skills API blueprint.
"""
from flask import Blueprint, request
from services.role_service import RoleService

roles_bp = Blueprint("roles_v1", __name__)


@roles_bp.get("/roles")
def list_roles():
    """List all available job roles."""
    from api import api_response
    roles = RoleService.list_roles()
    return api_response(data=roles)


@roles_bp.get("/roles/<int:rid>/skills")
def role_skills(rid):
    """
    Return the required skills for a role with dual-taxonomy breakdown.
    Query params:
        category: 'technical' | 'knowledge' | 'activity' | 'all' (default: 'all')
    """
    from api import api_response
    cat_filter = request.args.get("category", "all")
    result, err, status_code = RoleService.get_role_skills(rid, category_filter=cat_filter)
    if err:
        return api_response(message=err, status_code=status_code)
    return api_response(data=result)
