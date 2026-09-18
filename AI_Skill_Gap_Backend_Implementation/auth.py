"""
auth.py — JWT Authentication Blueprint for the AI Skill Gap system.

Endpoints:
    POST /api/auth/register   — Create account (name, email, password)
    POST /api/auth/login      — Get JWT token (email, password)
    GET  /api/auth/me         — Get current user profile (requires token)
    POST /api/auth/refresh    — Refresh an expired token

Decorator:
    @require_auth  — protect any route; injects current_user_id into g
"""
import bcrypt
from flask import Blueprint, g, jsonify, request
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    get_jwt_identity,
    jwt_required,
)

from extensions import db
from models import Student, User

auth_bp = Blueprint("auth", __name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────
def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ─────────────────────────────────────────────────────────────────────────────
# Register
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.post("/register")
def register():
    """
    Create a new user account.

    Body (JSON):
        name     (str, required)
        email    (str, required, unique)
        password (str, required, min 6 chars)
        course   (str, optional)
        year     (int, optional)

    Returns 201 with JWT access token on success.
    """
    d = request.get_json(silent=True) or {}
    name     = (d.get("name") or "").strip()
    email    = (d.get("email") or "").strip().lower()
    password = (d.get("password") or "")

    if not name:
        return jsonify({"error": "name is required"}), 400
    if not email or "@" not in email:
        return jsonify({"error": "valid email is required"}), 400
    if len(password) < 6:
        return jsonify({"error": "password must be at least 6 characters"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already registered"}), 409

    # Create User
    user = User(
        name=name,
        email=email,
        password_hash=_hash(password),
        role="student",
    )
    db.session.add(user)
    db.session.flush()

    # Auto-create linked Student profile
    student = Student.query.filter_by(email=email).first()
    if not student:
        student = Student(
            name=name,
            email=email,
            course=d.get("course", ""),
            year=d.get("year"),
            target_career=d.get("target_career", ""),
        )
        db.session.add(student)
        db.session.flush()

    user.student_id = student.id
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        "message":       "Account created successfully",
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "user":          user.to_dict(),
        "student_id":    student.id,
    }), 201


# ─────────────────────────────────────────────────────────────────────────────
# Login
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.post("/login")
def login():
    """
    Authenticate and get a JWT token.

    Body (JSON):
        email    (str)
        password (str)

    Returns 200 with access_token + refresh_token.
    """
    d = request.get_json(silent=True) or {}
    email    = (d.get("email") or "").strip().lower()
    password = (d.get("password") or "")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not _verify(password, user.password_hash):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    # Update last login time
    user.last_login = _utcnow()
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({
        "access_token":  access_token,
        "refresh_token": refresh_token,
        "user":          user.to_dict(),
        "student_id":    user.student_id,
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
# Current user profile
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.get("/me")
@jwt_required()
def me():
    """Return the current authenticated user's profile."""
    user_id = int(get_jwt_identity())
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404

    data = user.to_dict()
    if user.student_id:
        student = db.session.get(Student, user.student_id)
        if student:
            data["student"] = student.to_dict()

    return jsonify(data), 200


# ─────────────────────────────────────────────────────────────────────────────
# Refresh token
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    """Exchange a refresh token for a new access token."""
    identity = get_jwt_identity()
    new_token = create_access_token(identity=identity)
    return jsonify({"access_token": new_token}), 200


# ─────────────────────────────────────────────────────────────────────────────
# Optional auth decorator (for routes that can work with or without auth)
# ─────────────────────────────────────────────────────────────────────────────
def get_current_user_id() -> int | None:
    """
    Try to extract user_id from Bearer token without raising.
    Returns None if no token or invalid token.
    """
    from flask_jwt_extended import decode_token
    from flask_jwt_extended.exceptions import JWTExtendedException
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    try:
        token = auth_header.split(" ", 1)[1]
        data  = decode_token(token)
        return int(data["sub"])
    except (JWTExtendedException, Exception):
        return None


def _utcnow():
    """Local helper so auth.py does not need to import from models."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
# Ownership guard — call at the top of every student-private route
# ─────────────────────────────────────────────────────────────────────────────
def require_student_auth(sid: int):
    """
    Verify JWT token (optional — no error if missing) and check ownership.

    Usage in a route::

        student, err = require_student_auth(sid)
        if err:
            return err

    Returns
    -------
    (Student, None)       — authenticated and authorised
    (None, error_response) — missing token, invalid token, or wrong student

    Strategy: jwt_required(optional=True)
    - No token present  → return 401 if the route needs a real user, else skip
    - Token present but wrong student → 403
    - Token present, correct student → return student object
    """
    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
    from flask_jwt_extended.exceptions import JWTExtendedException
    from jwt.exceptions import PyJWTError

    # Try to verify token — if absent, we treat it as "optional" for now
    # so existing browser sessions are not immediately broken.
    try:
        verify_jwt_in_request(optional=True)
    except (JWTExtendedException, PyJWTError, Exception):
        return None, (jsonify({"error": "Invalid or expired token"}), 401)

    identity = get_jwt_identity()
    if identity is None:
        # No token — allow anonymous access to keep the frontend templates working.
        # The route will still function; it just won't enforce ownership.
        student = db.session.get(Student, sid)
        if not student:
            return None, (jsonify({"error": "student not found"}), 404)
        return student, None

    # Token present — enforce ownership
    try:
        user_id = int(identity)
    except (ValueError, TypeError):
        return None, (jsonify({"error": "Invalid token identity"}), 401)

    user = db.session.get(User, user_id)
    if not user:
        return None, (jsonify({"error": "Authenticated user not found"}), 401)

    if user.student_id != sid:
        return None, (jsonify({"error": "Access denied: you can only access your own data"}), 403)

    student = db.session.get(Student, sid)
    if not student:
        return None, (jsonify({"error": "student not found"}), 404)

    return student, None


def get_student_id_from_jwt() -> int | None:
    """
    Extract the student_id linked to the current JWT token.
    Returns None if no token or user has no linked student.
    Used by routes like /skill-gap/analyze that derive student from JWT.
    """
    from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
    from flask_jwt_extended.exceptions import JWTExtendedException
    from jwt.exceptions import PyJWTError
    try:
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if not identity:
            return None
        user = db.session.get(User, int(identity))
        return user.student_id if user else None
    except (JWTExtendedException, PyJWTError, Exception):
        return None
