"""
tests/test_onet_ingest.py — Unit tests for the O*NET dual-taxonomy integration.

Tests:
    1. Normalization formula: LV → required_level [1,5] → [20,100] proficiency scale
    2. Normalization formula: IM → importance [0.1, 1.0]
    3. ingest_onet() end-to-end with real XLSX files (skipped if files absent)
    4. Category filter on GET /api/roles/<id>/skills?category=
    5. JobRole.onet_code is populated after ingestion
    6. Idempotency: second run must not create duplicate records
"""
import re
import pytest
from pathlib import Path

# ── O*NET file presence check ─────────────────────────────────────────────────
_DATASET_DIR = Path(__file__).parents[4] / "Dataset"
ONET_KNOWLEDGE_PATH   = _DATASET_DIR / "Knowledge (1).xlsx"
ONET_ACTIVITIES_PATH  = _DATASET_DIR / "Work Activities (1).xlsx"
ONET_OCCUPATIONS_PATH = _DATASET_DIR / "Occupation Data (1).xlsx"
ONET_FILES_EXIST = (
    ONET_KNOWLEDGE_PATH.exists()
    and ONET_ACTIVITIES_PATH.exists()
    and ONET_OCCUPATIONS_PATH.exists()
)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Pure normalization formula tests (no DB needed)
# ═══════════════════════════════════════════════════════════════════════════════

class TestNormalizationFormulas:
    """Tests for the scale-conversion math defined in the PRD."""

    @pytest.mark.parametrize("lv,expected", [
        (0.0,  3),   # zero or negative → default mid-range 3
        (1.0,  1),   # 1/7 * 5 = 0.71 → round → 1
        (7.0,  5),   # max → 5
        (6.0,  4),   # 6/7 * 5 = 4.28 → round → 4
        (10.0, 5),   # above max → clamped to 5
    ])
    def test_lv_to_required_level(self, lv, expected):
        """required_level = round(LV/7.0 * 5.0) if LV > 0 else 3, clamped to [1,5]."""
        raw = round((lv / 7.0) * 5.0) if lv > 0 else 3
        result = max(1, min(5, raw))
        assert result == expected

    @pytest.mark.parametrize("lv,expected", [
        (0.0,  60.0),
        (7.0, 100.0),
        (1.0,  20.0),
        (6.0,  80.0),
    ])
    def test_lv_to_proficiency_100_scale(self, lv, expected):
        """proficiency (0–100) = req_level * 20."""
        raw = round((lv / 7.0) * 5.0) if lv > 0 else 3
        result = float(max(1, min(5, raw))) * 20.0
        assert result == expected

    @pytest.mark.parametrize("im,expected", [
        (5.0,  1.0),
        (2.5,  0.5),
        (0.0,  0.1),
        (1.0,  0.2),
        (3.0,  0.6),
        (6.0,  1.0),
        (-1.0, 0.1),
    ])
    def test_im_to_importance(self, im, expected):
        """importance = clamp(IM/5.0, 0.1, 1.0)."""
        result = min(1.0, max(0.1, im / 5.0))
        assert abs(result - expected) < 1e-9

    def test_importance_always_in_range(self):
        for im in [-10, 0, 0.001, 1, 2.5, 4.9, 5, 7, 100]:
            result = min(1.0, max(0.1, im / 5.0))
            assert 0.1 <= result <= 1.0

    def test_required_level_always_in_range(self):
        for lv in [-5, 0, 0.5, 1, 3, 5, 7, 10]:
            raw = round((lv / 7.0) * 5.0) if lv > 0 else 3
            result = max(1, min(5, raw))
            assert 1 <= result <= 5


# ═══════════════════════════════════════════════════════════════════════════════
# 2. DB-backed ingestion tests (skipped when files absent)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(not ONET_FILES_EXIST, reason="O*NET XLSX files not present in Dataset/")
class TestOnetIngestion:

    def _run_onet(self, app):
        from data.ingest import ingest_onet, ingest_esco
        from config import Config
        ingest_esco(Config.ESCO_DATA_DIR)
        return ingest_onet(
            knowledge_path=str(ONET_KNOWLEDGE_PATH),
            activities_path=str(ONET_ACTIVITIES_PATH),
            occupations_path=str(ONET_OCCUPATIONS_PATH),
        )

    def test_returns_valid_summary(self, app):
        with app.app_context():
            result = self._run_onet(app)
            assert isinstance(result, dict)
            for key in ("skills", "job_skills", "roles_updated"):
                assert key in result and result[key] >= 0

    def test_onet_skills_have_correct_category(self, app):
        with app.app_context():
            self._run_onet(app)
            from models import Skill
            onet_skills = Skill.query.filter_by(source="O*NET").all()
            assert len(onet_skills) > 0
            valid = {"O*NET Knowledge", "O*NET Work Activity"}
            for sk in onet_skills:
                assert sk.category in valid, f"Unexpected category: {sk.category} for '{sk.name}'"

    def test_required_level_in_valid_range(self, app):
        with app.app_context():
            self._run_onet(app)
            from models import JobSkill
            rows = JobSkill.query.filter_by(source="O*NET").all()
            assert len(rows) > 0
            for js in rows:
                assert 20.0 <= js.required_level <= 100.0, \
                    f"required_level={js.required_level} out of [20, 100]"

    def test_importance_in_valid_range(self, app):
        with app.app_context():
            self._run_onet(app)
            from models import JobSkill
            for js in JobSkill.query.filter_by(source="O*NET").all():
                assert 0.1 <= js.importance <= 1.0, \
                    f"importance={js.importance} out of [0.1, 1.0]"

    def test_jobrole_onet_code_populated(self, app):
        with app.app_context():
            self._run_onet(app)
            from models import JobRole
            roles = JobRole.query.filter(JobRole.onet_code.isnot(None)).all()
            assert len(roles) > 0
            for role in roles:
                assert re.match(r"^\d{2}-\d{4}\.\d{2}$", role.onet_code), \
                    f"Invalid SOC code format: '{role.onet_code}'"

    def test_idempotent(self, app):
        with app.app_context():
            self._run_onet(app)
            from models import Skill, JobSkill
            c1_sk = Skill.query.filter_by(source="O*NET").count()
            c1_js = JobSkill.query.filter_by(source="O*NET").count()
            self._run_onet(app)
            c2_sk = Skill.query.filter_by(source="O*NET").count()
            c2_js = JobSkill.query.filter_by(source="O*NET").count()
            assert c1_sk == c2_sk, f"Duplicate O*NET skills: {c1_sk} → {c2_sk}"
            assert c1_js == c2_js, f"Duplicate O*NET JobSkill: {c1_js} → {c2_js}"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. API Category Filter Tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture()
def dual_role_id(app):
    """Seed a role with ESCO + O*NET skills; return the role id."""
    with app.app_context():
        from extensions import db
        from models import JobRole, Skill, JobSkill
        import uuid
        suffix = uuid.uuid4().hex[:6]
        role = JobRole(
            name=f"Test Dual Taxonomy Role {suffix}", source="DEMO",
            source_identifier=f"test-uri-dual-{suffix}", onet_code="15-1252.00"
        )
        db.session.add(role)
        db.session.flush()

        skills_data = [
            (f"OnetTestEscoSkill-{suffix}",     "Programming",         "ESCO"),
            (f"OnetTestKnowledge-{suffix}",     "O*NET Knowledge",     "O*NET"),
            (f"OnetTestWorkActivity-{suffix}",  "O*NET Work Activity", "O*NET"),
        ]
        for name, cat, src in skills_data:
            sk = Skill(name=name, category=cat, source=src)
            db.session.add(sk)
            db.session.flush()
            db.session.add(JobSkill(
                job_role_id=role.id, skill_id=sk.id,
                required_level=60.0, importance=0.8, source=src
            ))
        db.session.commit()
        return role.id


class TestRoleSkillsCategoryFilter:

    def test_default_returns_all(self, client, app, dual_role_id):
        with app.app_context():
            r = client.get(f"/api/roles/{dual_role_id}/skills")
            assert r.status_code == 200
            data = r.get_json()
            assert data["total_skills"] == 3
            assert data["filtered_count"] == 3

    def test_technical_filter(self, client, app, dual_role_id):
        with app.app_context():
            r = client.get(f"/api/roles/{dual_role_id}/skills?category=technical")
            assert r.status_code == 200
            data = r.get_json()
            assert data["filtered_count"] == 1
            assert all("o*net" not in (s["category"] or "").lower()
                       for s in data["required_skills"])

    def test_knowledge_filter(self, client, app, dual_role_id):
        with app.app_context():
            r = client.get(f"/api/roles/{dual_role_id}/skills?category=knowledge")
            assert r.status_code == 200
            data = r.get_json()
            assert data["filtered_count"] == 1
            assert data["required_skills"][0]["category"] == "O*NET Knowledge"

    def test_activity_filter(self, client, app, dual_role_id):
        with app.app_context():
            r = client.get(f"/api/roles/{dual_role_id}/skills?category=activity")
            assert r.status_code == 200
            data = r.get_json()
            assert data["filtered_count"] == 1
            assert data["required_skills"][0]["category"] == "O*NET Work Activity"

    def test_taxonomy_counts_in_response(self, client, app, dual_role_id):
        with app.app_context():
            r = client.get(f"/api/roles/{dual_role_id}/skills")
            data = r.get_json()
            assert data["technical_skills_count"]  == 1
            assert data["onet_competencies_count"] == 2

    def test_onet_code_and_esco_uri_in_response(self, client, app, dual_role_id):
        with app.app_context():
            r = client.get(f"/api/roles/{dual_role_id}/skills")
            data = r.get_json()
            assert data["onet_code"] == "15-1252.00"
            assert "test-uri-dual-" in data["esco_uri"]

    def test_invalid_role_404(self, client, app):
        with app.app_context():
            r = client.get("/api/roles/999999/skills")
            assert r.status_code == 404
