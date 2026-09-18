"""
schemas/learning_schemas.py — Validation schemas for Learning Path and Progress endpoints.
"""
from marshmallow import Schema, fields, validate


class LearningPathGenerateSchema(Schema):
    job_role_id = fields.Integer(required=True)
    career_goal = fields.String(load_default="")


class LearningProgressSchema(Schema):
    course_id = fields.Integer(required=True)
    status = fields.String(
        required=True,
        validate=validate.OneOf(["not_started", "in_progress", "completed"])
    )
    progress_pct = fields.Float(
        validate=validate.Range(min=0.0, max=100.0),
        load_default=None
    )
    time_spent_mins = fields.Integer(
        validate=validate.Range(min=0),
        load_default=0
    )
