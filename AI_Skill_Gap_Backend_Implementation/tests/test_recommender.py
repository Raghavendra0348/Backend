"""tests/test_recommender.py — Unit tests for the content-based recommender."""
import pytest


class TestRecommender:
    def test_returns_list(self, client, app_ctx):
        """recommend() returns a list."""
        from models import Student, StudentSkill, JobRole, Skill
        from extensions import db
        from services.gap_engine import analyze
        from services.recommender import recommend

        with app_ctx.app_context():
            s = Student(name="RecTest", email="rectest@example.com",
                        course="MCA", year=2)
            db.session.add(s)
            db.session.flush()

            # Student is missing several skills → will have gaps → recommendations
            role = JobRole.query.filter_by(name="Software Developer").first()
            skill = Skill.query.filter_by(name="Python").first()
            db.session.add(StudentSkill(
                student_id=s.id, skill_id=skill.id,
                proficiency=40, evidence_type="self_reported"
            ))
            db.session.commit()

            analyze(s.id, role.id)   # Generate skill gaps first
            recs = recommend(s.id, top_k=5)

        assert isinstance(recs, list)

    def test_fields_present(self, client, app_ctx):
        """Each recommendation must include required fields."""
        from models import Student, JobRole
        from extensions import db
        from services.gap_engine import analyze
        from services.recommender import recommend

        with app_ctx.app_context():
            s = Student(name="FieldRec", email="fieldrec@example.com",
                        course="MCA", year=2)
            db.session.add(s)
            db.session.commit()
            role = JobRole.query.filter_by(name="Software Developer").first()
            analyze(s.id, role.id)
            recs = recommend(s.id, top_k=10)

        required = {"skill_id", "skill", "course_id", "title", "score", "reason"}
        for r in recs:
            assert required.issubset(set(r.keys())), f"Missing fields in {r}"

    def test_score_range(self, client, app_ctx):
        """Scores must be in [0, 1]."""
        from models import Student, JobRole
        from extensions import db
        from services.gap_engine import analyze
        from services.recommender import recommend

        with app_ctx.app_context():
            s = Student(name="ScoreTest", email="scoretest@example.com",
                        course="MCA", year=2)
            db.session.add(s)
            db.session.commit()
            role = JobRole.query.filter_by(name="Software Developer").first()
            analyze(s.id, role.id)
            recs = recommend(s.id, top_k=10)

        for r in recs:
            assert 0.0 <= r["score"] <= 1.0, f"Score out of range: {r['score']}"

    def test_scores_descending(self, client, app_ctx):
        """Recommendations must be sorted by score descending."""
        from models import Student, JobRole
        from extensions import db
        from services.gap_engine import analyze
        from services.recommender import recommend

        with app_ctx.app_context():
            s = Student(name="SortRec", email="sortrec@example.com",
                        course="MCA", year=2)
            db.session.add(s)
            db.session.commit()
            role = JobRole.query.filter_by(name="Software Developer").first()
            analyze(s.id, role.id)
            recs = recommend(s.id, top_k=10)

        scores = [r["score"] for r in recs]
        assert scores == sorted(scores, reverse=True)

    def test_top_k_respected(self, client, app_ctx):
        """recommend(top_k=3) should return at most 3 results."""
        from models import Student, JobRole
        from extensions import db
        from services.gap_engine import analyze
        from services.recommender import recommend

        with app_ctx.app_context():
            s = Student(name="TopKRec", email="topkrec@example.com",
                        course="MCA", year=2)
            db.session.add(s)
            db.session.commit()
            role = JobRole.query.filter_by(name="Software Developer").first()
            analyze(s.id, role.id)
            recs = recommend(s.id, top_k=3)

        assert len(recs) <= 3

    def test_no_gap_no_required_recs(self, client, app_ctx):
        """Student with no skill gaps should have no gap-driven recommendations."""
        from models import Student, StudentSkill, JobRole, JobSkill
        from extensions import db
        from services.gap_engine import analyze
        from services.recommender import recommend

        with app_ctx.app_context():
            s = Student(name="FullSkill", email="fullskill@example.com",
                        course="MCA", year=2)
            db.session.add(s)
            db.session.flush()
            role = JobRole.query.filter_by(name="Software Developer").first()
            reqs = JobSkill.query.filter_by(job_role_id=role.id).all()
            for req in reqs:
                db.session.add(StudentSkill(
                    student_id=s.id, skill_id=req.skill_id,
                    proficiency=req.required_level + 10,
                    evidence_type="self_reported"
                ))
            db.session.commit()
            analyze(s.id, role.id)
            recs = recommend(s.id, top_k=10)

        # All gaps are 0 so no recommendations should be returned
        assert recs == []
