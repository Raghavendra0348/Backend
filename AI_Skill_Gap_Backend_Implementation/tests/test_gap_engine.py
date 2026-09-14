"""tests/test_gap_engine.py — Unit tests for gap classification and analysis."""
import pytest
from services.gap_engine import classify_gap


# ── classify_gap ─────────────────────────────────────────────────────────────
class TestClassifyGap:
    def test_low_boundary(self):
        assert classify_gap(0) == "LOW"

    def test_low_exact_threshold(self):
        assert classify_gap(20.0) == "LOW"

    def test_low_below_threshold(self):
        assert classify_gap(10) == "LOW"

    def test_medium_just_above_low(self):
        assert classify_gap(21) == "MEDIUM"

    def test_medium_midpoint(self):
        assert classify_gap(35) == "MEDIUM"

    def test_medium_exact_threshold(self):
        assert classify_gap(50.0) == "MEDIUM"

    def test_high_just_above_medium(self):
        assert classify_gap(51) == "HIGH"

    def test_high_extreme(self):
        assert classify_gap(100) == "HIGH"

    def test_high_seventy(self):
        assert classify_gap(70) == "HIGH"


# ── Full gap analysis with DB ─────────────────────────────────────────────────
class TestAnalyze:
    def test_analyze_returns_list(self, client, app_ctx):
        """analyze() returns a list for a student with skills vs role requirements."""
        from models import Student, StudentSkill, JobRole, Skill
        from extensions import db
        from services.gap_engine import analyze

        with app_ctx.app_context():
            # Create a test student
            s = Student(name="Test User", email="testgap@example.com",
                        course="MCA", year=2)
            db.session.add(s)
            db.session.flush()

            skill = Skill.query.filter_by(name="Python").first()
            db.session.add(StudentSkill(
                student_id=s.id, skill_id=skill.id,
                proficiency=50, evidence_type="self_reported"
            ))
            db.session.commit()

            role = JobRole.query.filter_by(name="Software Developer").first()
            gaps = analyze(s.id, role.id)

        assert isinstance(gaps, list)
        assert len(gaps) > 0

    def test_gap_fields_present(self, client, app_ctx):
        """Each gap dict must have all required fields."""
        from models import Student, StudentSkill, JobRole, Skill
        from extensions import db
        from services.gap_engine import analyze

        with app_ctx.app_context():
            s = Student(name="FieldTest", email="fieldtest@example.com",
                        course="MCA", year=2)
            db.session.add(s)
            db.session.flush()
            skill = Skill.query.filter_by(name="SQL").first()
            db.session.add(StudentSkill(
                student_id=s.id, skill_id=skill.id,
                proficiency=60, evidence_type="self_reported"
            ))
            db.session.commit()
            role = JobRole.query.filter_by(name="Software Developer").first()
            gaps = analyze(s.id, role.id)

        required_fields = {
            "skill_id", "current_level", "required_level",
            "gap", "gap_percent", "severity", "priority_score"
        }
        for g in gaps:
            assert required_fields.issubset(set(g.keys()))

    def test_no_gap_when_proficient(self, client, app_ctx):
        """Student with proficiency >= required should have gap=0."""
        from models import Student, StudentSkill, JobRole, Skill, JobSkill
        from extensions import db
        from services.gap_engine import analyze

        with app_ctx.app_context():
            s = Student(name="ProficientUser", email="proficient@example.com",
                        course="MCA", year=2)
            db.session.add(s)
            db.session.flush()

            role = JobRole.query.filter_by(name="Software Developer").first()
            skills_reqs = JobSkill.query.filter_by(job_role_id=role.id).all()
            for req in skills_reqs:
                db.session.add(StudentSkill(
                    student_id=s.id, skill_id=req.skill_id,
                    proficiency=req.required_level + 5,
                    evidence_type="self_reported"
                ))
            db.session.commit()

            gaps = analyze(s.id, role.id)

        for g in gaps:
            assert g["gap"] == 0.0

    def test_priority_ordering(self, client, app_ctx):
        """Gaps are sorted by priority_score descending."""
        from models import Student, StudentSkill, JobRole
        from extensions import db
        from services.gap_engine import analyze

        with app_ctx.app_context():
            s = Student(name="OrderTest", email="order@example.com",
                        course="MCA", year=2)
            db.session.add(s)
            db.session.commit()
            role = JobRole.query.filter_by(name="Software Developer").first()
            gaps = analyze(s.id, role.id)

        priorities = [g["priority_score"] for g in gaps]
        assert priorities == sorted(priorities, reverse=True)

    def test_empty_role_returns_empty(self, client, app_ctx):
        """analyze() for a role with no job_skills returns empty list."""
        from models import Student, JobRole
        from extensions import db
        from services.gap_engine import analyze

        with app_ctx.app_context():
            empty_role = JobRole(name="Empty Role", source="DEMO",
                                 source_identifier="empty-demo")
            db.session.add(empty_role)
            s = Student(name="EmptyTest", email="empty@example.com",
                        course="MCA", year=2)
            db.session.add(s)
            db.session.commit()
            gaps = analyze(s.id, empty_role.id)

        assert gaps == []
