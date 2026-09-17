"""
tests/test_skill_normalizer.py — Tests for skill canonicalization, alias equivalence,
and essential vs optional skill handling in GapEngine and RoleMatcher.
"""
import pytest
from app import create_app
from extensions import db
import uuid
from models import JobRole, JobSkill, Skill, Student, StudentSkill, SkillGap
from services.skill_normalizer import (
    canonicalize_skill_name,
    clean_skill_str,
    get_equivalent_skill_ids,
    SKILL_ALIAS_MAP,
)
from services import gap_engine, role_matcher


# ─────────────────────────────────────────────────────────────────────────────
# Unit Tests: Canonicalization Rules
# ─────────────────────────────────────────────────────────────────────────────
class TestSkillCanonicalization:
    def test_css_variations(self):
        assert canonicalize_skill_name("css") == "CSS3"
        assert canonicalize_skill_name("CSS") == "CSS3"
        assert canonicalize_skill_name("css3") == "CSS3"
        assert canonicalize_skill_name("css5") == "CSS3"
        assert canonicalize_skill_name("CSS 3") == "CSS3"
        assert canonicalize_skill_name("flexbox") == "CSS3"
        assert canonicalize_skill_name("box css") == "CSS3"
        assert canonicalize_skill_name("css grid") == "CSS3"
        assert canonicalize_skill_name("cascading style sheets") == "CSS3"

    def test_html_variations(self):
        assert canonicalize_skill_name("html") == "HTML5"
        assert canonicalize_skill_name("html5") == "HTML5"
        assert canonicalize_skill_name("semantic html") == "HTML5"

    def test_javascript_variations(self):
        assert canonicalize_skill_name("js") == "JavaScript"
        assert canonicalize_skill_name("javascript") == "JavaScript"
        assert canonicalize_skill_name("es6") == "JavaScript"
        assert canonicalize_skill_name("ecmascript") == "JavaScript"

    def test_python_variations(self):
        assert canonicalize_skill_name("python") == "Python"
        assert canonicalize_skill_name("python3") == "Python"
        assert canonicalize_skill_name("py3") == "Python"
        assert canonicalize_skill_name("python 3.10") == "Python"

    def test_devops_and_cloud(self):
        assert canonicalize_skill_name("k8s") == "Kubernetes"
        assert canonicalize_skill_name("kubernetes") == "Kubernetes"
        assert canonicalize_skill_name("docker") == "Docker"
        assert canonicalize_skill_name("docker containers") == "Docker"
        assert canonicalize_skill_name("aws") == "AWS / Azure / GCP"

    def test_database_variations(self):
        assert canonicalize_skill_name("sql") == "SQL"
        assert canonicalize_skill_name("postgres") == "PostgreSQL"
        assert canonicalize_skill_name("postgresql") == "PostgreSQL"
        assert canonicalize_skill_name("mongo") == "MongoDB"

    def test_clean_skill_str(self):
        assert clean_skill_str("   Python   3.9  ") == "Python 3.9"
        assert clean_skill_str("") == ""
        assert clean_skill_str(None) == ""


# ─────────────────────────────────────────────────────────────────────────────
# Integration Tests: Equivalence Resolution in Gap Engine & Role Matcher
# ─────────────────────────────────────────────────────────────────────────────
class TestSkillEquivalenceInEngine:
    @pytest.fixture
    def app_ctx(self):
        app = create_app()
        app.config["TESTING"] = True
        with app.app_context():
            yield app

    def test_student_with_css_satisfies_css3_requirement(self, app_ctx):
        """Entering 'CSS' gives student credit toward 'CSS3' requirement with 0 gap."""
        u_email = f"webdev_{uuid.uuid4().hex[:8]}@example.com"
        student = Student(name="Test Web Dev", email=u_email)
        db.session.add(student)
        db.session.flush()

        try:
            # Ensure role exists with CSS3 requirement
            role = JobRole.query.filter_by(name="Web Developer").first()
            assert role is not None, "Web Developer role must exist"

            css3_skill = Skill.query.filter(db.func.lower(Skill.name) == "css3").first()
            assert css3_skill is not None, "CSS3 skill must exist"

            # Student has 'CSS3' (or an alias) at 80 proficiency
            db.session.add(StudentSkill(
                student_id=student.id,
                skill_id=css3_skill.id,
                proficiency=80.0,
                evidence_type="self_reported",
            ))
            db.session.commit()

            # Run gap analysis
            gaps = gap_engine.analyze(student.id, role.id)
            css_gap = next((g for g in gaps if g["skill_id"] == css3_skill.id), None)
            assert css_gap is not None
            assert css_gap["current_level"] == 80.0
            assert css_gap["gap"] == 0.0
            assert css_gap["severity"] == "LOW"
        finally:
            SkillGap.query.filter_by(student_id=student.id).delete()
            StudentSkill.query.filter_by(student_id=student.id).delete()
            db.session.delete(student)
            db.session.commit()

    def test_essential_vs_optional_metadata_in_gaps(self, app_ctx):
        """Gap analysis correctly includes relation_type (essential vs optional)."""
        u_email = f"meta_dev_{uuid.uuid4().hex[:8]}@example.com"
        student = Student(name="Test Metadata Dev", email=u_email)
        db.session.add(student)
        db.session.flush()

        try:
            role = JobRole.query.filter_by(name="Web Developer").first()
            gaps = gap_engine.analyze(student.id, role.id)

            essential_gaps = [g for g in gaps if g["relation_type"] == "essential"]
            optional_gaps = [g for g in gaps if g["relation_type"] == "optional"]

            assert len(essential_gaps) == 10
            assert len(optional_gaps) == 5
            assert len(gaps) == 15

            # Optional gaps have lower priority score than equivalent essential gaps
            for eg in essential_gaps:
                assert eg["priority_score"] > 0
            for og in optional_gaps:
                assert og["priority_score"] > 0
        finally:
            SkillGap.query.filter_by(student_id=student.id).delete()
            db.session.delete(student)
            db.session.commit()

    def test_api_add_skill_auto_canonicalizes(self, client):
        """POST /students/<id>/skills with 'css' maps to canonical 'CSS3'."""
        u_email = f"api_norm_{uuid.uuid4().hex[:8]}@example.com"
        resp = client.post("/api/students", json={
            "name": "API Normalizer Student",
            "email": u_email,
            "course": "CSE",
            "year": 4,
            "target_career": "Web Developer"
        })
        assert resp.status_code == 201
        sid = resp.get_json()["id"]

        try:
            # Add skill with raw input 'css'
            resp_skill = client.post(f"/api/students/{sid}/skills", json={
                "skill_name": "css",
                "proficiency": 85.0
            })
            assert resp_skill.status_code == 201

            # Verify StudentSkill is attached to CSS3
            ss = StudentSkill.query.filter_by(student_id=sid).first()
            skill_obj = db.session.get(Skill, ss.skill_id)
            assert skill_obj.name == "CSS3"
        finally:
            StudentSkill.query.filter_by(student_id=sid).delete()
            Student.query.filter_by(id=sid).delete()
            db.session.commit()
