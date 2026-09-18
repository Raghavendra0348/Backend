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

    def test_configurable_weights(self, client, app_ctx):
        """Custom weights should be normalized and applied."""
        from models import Student, JobRole
        from extensions import db
        from services.gap_engine import analyze
        from services.recommender import recommend, normalize_weights

        weights = normalize_weights({"quality": 0.8, "content_similarity": 0.2})
        assert abs(sum(weights.values()) - 1.0) < 1e-3

        with app_ctx.app_context():
            s = Student(name="WeightsRec", email="weightsrec@example.com", course="MCA", year=2)
            db.session.add(s)
            db.session.commit()
            role = JobRole.query.filter_by(name="Software Developer").first()
            analyze(s.id, role.id)
            recs = recommend(s.id, top_k=5, weights={"quality": 0.9, "skill_gap_relevance": 0.1})

        assert len(recs) > 0
        for r in recs:
            assert "level_fit" in r

    def test_completed_course_excluded_by_user_preference(self, client, app_ctx):
        """Courses already completed by student must be excluded from recommendations."""
        from models import Student, JobRole, Course, LearningProgress
        from extensions import db
        from services.gap_engine import analyze
        from services.recommender import recommend

        with app_ctx.app_context():
            s = Student(name="CompletedRec", email="completedrec@example.com", course="MCA", year=2)
            db.session.add(s)
            db.session.commit()
            role = JobRole.query.filter_by(name="Software Developer").first()
            analyze(s.id, role.id)

            # Get default recommendations
            initial_recs = recommend(s.id, top_k=5)
            assert len(initial_recs) > 0
            first_course_id = initial_recs[0]["course_id"]

            # Mark this course as completed
            db.session.add(LearningProgress(
                student_id=s.id,
                course_id=first_course_id,
                title=initial_recs[0]["title"],
                status="completed",
                completion=100.0
            ))
            db.session.commit()

            # Next recommendation run must exclude this course
            updated_recs = recommend(s.id, top_k=5)
            rec_course_ids = [r["course_id"] for r in updated_recs]
            assert first_course_id not in rec_course_ids

    def test_recommendation_runs_snapshot_persisted(self, client, app_ctx):
        """Recommendation generation should snapshot run history in recommendation_runs."""
        from models import Student, JobRole
        from extensions import db
        from services.gap_engine import analyze
        from services.recommender import recommend, get_recommendation_runs

        with app_ctx.app_context():
            s = Student(name="SnapshotRec", email="snapshotrec@example.com", course="MCA", year=2)
            db.session.add(s)
            db.session.commit()
            role = JobRole.query.filter_by(name="Software Developer").first()
            analyze(s.id, role.id)
            recommend(s.id, top_k=5)

            runs = get_recommendation_runs(s.id)
            assert len(runs) >= 1
            assert "weights_used" in runs[0]
            assert "recommendations_snapshot" in runs[0]
            assert len(runs[0]["recommendations_snapshot"]) > 0

