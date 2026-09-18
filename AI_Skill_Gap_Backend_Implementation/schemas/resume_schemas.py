"""
schemas/resume_schemas.py — Validation schemas for Project and Certification endpoints.
"""
from marshmallow import Schema, fields, validate


class ProjectCreateSchema(Schema):
    title = fields.String(required=True, validate=validate.Length(min=1, max=150))
    description = fields.String(load_default="")
    skills_used = fields.Raw(load_default="")  # string or list of strings
    github_url = fields.String(load_default="")
    live_url = fields.String(load_default="")


class CertificationCreateSchema(Schema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=150))
    issuer = fields.String(load_default="")
    issue_date = fields.String(load_default=None)
    credential_id = fields.String(load_default="")
    credential_url = fields.String(load_default="")


class SkillVerificationItemSchema(Schema):
    evidence_id = fields.Integer(required=True)
    action = fields.String(required=True, validate=validate.OneOf(["accept", "reject"]))
    proficiency = fields.Float(load_default=50.0, validate=validate.Range(min=0.0, max=100.0))


class SkillVerificationListSchema(Schema):
    verifications = fields.List(
        fields.Nested(SkillVerificationItemSchema),
        required=True,
        validate=validate.Length(min=1)
    )

