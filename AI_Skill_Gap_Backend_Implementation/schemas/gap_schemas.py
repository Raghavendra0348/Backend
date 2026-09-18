"""
schemas/gap_schemas.py — Validation schemas for Gap Analysis endpoints.
"""
from marshmallow import Schema, fields, validates_schema, ValidationError


class GapAnalyzeSchema(Schema):
    job_role_id = fields.Integer(allow_none=True)
    role_id = fields.Integer(allow_none=True)
    student_id = fields.Integer(allow_none=True)

    @validates_schema
    def validate_role(self, data, **kwargs):
        if not data.get("job_role_id") and not data.get("role_id"):
            raise ValidationError("job_role_id (or role_id) is required")
