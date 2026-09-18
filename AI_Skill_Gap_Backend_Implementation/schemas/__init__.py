"""
schemas/__init__.py — Request input validation schemas for AI Skill Gap Backend.
Uses Marshmallow for declarative schema definitions and validation error handling.
"""
from functools import wraps
from flask import request, jsonify
from marshmallow import ValidationError


def validate_json(schema_cls):
    """
    Decorator to validate incoming JSON against a Marshmallow schema.
    Injects validated data into kwargs as 'validated_data' or returns 400 Bad Request.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            raw_data = request.get_json(silent=True)
            if raw_data is None:
                return jsonify({
                    "success": False,
                    "error": "Bad Request",
                    "detail": "JSON body is required"
                }), 400
            schema = schema_cls()
            try:
                validated = schema.load(raw_data)
            except ValidationError as err:
                return jsonify({
                    "success": False,
                    "error": "Validation Error",
                    "messages": err.messages
                }), 400
            kwargs["validated_data"] = validated
            return fn(*args, **kwargs)
        return wrapper
    return decorator
