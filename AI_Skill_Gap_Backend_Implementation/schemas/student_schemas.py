"""
schemas/student_schemas.py — Validation schemas for Student and Skill endpoints.
"""
from marshmallow import Schema, fields, validate, validates_schema, ValidationError


class StudentCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
    course = fields.String(load_default="")
    year = fields.Integer(validate=validate.Range(min=1, max=10), allow_none=True)
    target_career = fields.String(load_default="")


class StudentUpdateSchema(Schema):
    name = fields.String(validate=validate.Length(min=1, max=100))
    email = fields.Email()
    course = fields.String()
    year = fields.Integer(validate=validate.Range(min=1, max=10), allow_none=True)
    target_career = fields.String()


class SkillAddSchema(Schema):
    skill_id = fields.Integer(allow_none=True)
    skill_name = fields.String(allow_none=True)
    proficiency = fields.Float(
        required=True,
        validate=validate.Range(min=0.0, max=100.0)
    )
    source = fields.String(load_default="manual")

    @validates_schema
    def validate_identification(self, data, **kwargs):
        if not data.get("skill_id") and not data.get("skill_name"):
            raise ValidationError("Either skill_id or skill_name must be provided")
