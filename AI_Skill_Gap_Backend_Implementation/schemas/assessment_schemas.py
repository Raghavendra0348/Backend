"""
schemas/assessment_schemas.py — Validation schemas for Assessment endpoints.
"""
from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class AssessmentSubmitSchema(Schema):
    skill_id = fields.Integer(allow_none=True)
    skill_name = fields.String(allow_none=True)
    score = fields.Float(
        required=True,
        validate=validate.Range(min=0.0, max=100.0)
    )
    source = fields.String(load_default="mcq_test")
    test_title = fields.String(load_default="")

    @validates_schema
    def validate_skill(self, data, **kwargs):
        if not data.get("skill_id") and not data.get("skill_name"):
            raise ValidationError("Either skill_id or skill_name must be provided")


class ReassessmentSkillItemSchema(Schema):
    skill_id = fields.Integer(allow_none=True)
    skill_name = fields.String(allow_none=True)
    new_score = fields.Float(
        required=True,
        validate=validate.Range(min=0.0, max=100.0)
    )


class ReassessmentSubmitSchema(Schema):
    job_role_id = fields.Integer(allow_none=True)
    skills = fields.List(fields.Nested(ReassessmentSkillItemSchema), load_default=list)
    # Also support single-skill reassessment directly in payload
    skill_id = fields.Integer(allow_none=True)
    skill_name = fields.String(allow_none=True)
    new_score = fields.Float(validate=validate.Range(min=0.0, max=100.0), allow_none=True)
