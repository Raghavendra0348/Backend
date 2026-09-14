"""
tests/test_api.py — End-to-end API integration tests.

Covers the complete student journey:
  Register → Add Skills → Assessment → Role Mapping → Gap Analysis
  → Recommendations → Progress → Reassessment → Dashboard
"""
import json
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────
class TestHealth:
    def test_health_ok(self, client):
        rv = client.get("/api/health")
        assert rv.status_code == 200
        assert rv.get_json()["status"] == "ok"


# ─────────────────────────────────────────────────────────────────────────────
# Student CRUD
# ─────────────────────────────────────────────────────────────────────────────
class TestStudentCRUD:
    def test_create_student(self, client):
        rv = client.post("/api/students", json={
            "name": "Rahul Sharma", "email": "rahul@test.com",
            "course": "MCA", "year": 2, "target_career": "Software Developer"
        })
        assert rv.status_code == 201
        data = rv.get_json()
        assert "id" in data

    def test_create_student_missing_fields(self, client):
        rv = client.post("/api/students", json={"name": "Incomplete"})
        assert rv.status_code == 400

    def test_duplicate_email(self, client):
        client.post("/api/students", json={
            "name": "Duplicate User", "email": "dup@test.com"
        })
        rv = client.post("/api/students", json={
            "name": "Duplicate User 2", "email": "dup@test.com"
        })
        assert rv.status_code == 409

    def test_get_student(self, client):
        rv = client.post("/api/students", json={
            "name": "Get Test", "email": "get@test.com", "course": "MCA", "year": 3
        })
        sid = rv.get_json()["id"]
        rv2 = client.get(f"/api/students/{sid}")
        assert rv2.status_code == 200
        data = rv2.get_json()
        assert data["name"] == "Get Test"
        assert "skills" in data

    def test_get_student_not_found(self, client):
        rv = client.get("/api/students/99999")
        assert rv.status_code == 404

    def test_update_student(self, client):
        rv = client.post("/api/students", json={
            "name": "Update Test", "email": "update@test.com"
        })
        sid = rv.get_json()["id"]
        rv2 = client.put(f"/api/students/{sid}", json={"year": 4})
        assert rv2.status_code == 200
        assert rv2.get_json()["year"] == 4


# ─────────────────────────────────────────────────────────────────────────────
# Skills
# ─────────────────────────────────────────────────────────────────────────────
class TestSkills:
    def _create_student(self, client, suffix="skills"):
        rv = client.post("/api/students", json={
            "name": f"SkillStudent {suffix}",
            "email": f"skillstudent_{suffix}@test.com"
        })
        return rv.get_json()["id"]

    def _get_skill_id(self, client):
        """Get an existing skill id from the roles endpoint."""
        rv = client.get("/api/roles")
        roles = rv.get_json()
        if not roles:
            pytest.skip("No roles available")
        rv2 = client.get(f"/api/roles/{roles[0]['id']}/skills")
        skills = rv2.get_json()["required_skills"]
        if not skills:
            pytest.skip("No skills in role")
        return skills[0]["skill_id"]

    def test_add_skill(self, client):
        sid = self._create_student(client, "add")
        skill_id = self._get_skill_id(client)
        rv = client.post(f"/api/students/{sid}/skills", json={
            "skill_id": skill_id, "proficiency": 70
        })
        assert rv.status_code == 201

    def test_proficiency_out_of_range(self, client):
        sid = self._create_student(client, "range")
        skill_id = self._get_skill_id(client)
        rv = client.post(f"/api/students/{sid}/skills", json={
            "skill_id": skill_id, "proficiency": 150
        })
        assert rv.status_code == 400

    def test_update_existing_skill(self, client):
        sid = self._create_student(client, "update")
        skill_id = self._get_skill_id(client)
        client.post(f"/api/students/{sid}/skills", json={
            "skill_id": skill_id, "proficiency": 50
        })
        rv = client.post(f"/api/students/{sid}/skills", json={
            "skill_id": skill_id, "proficiency": 80
        })
        assert rv.status_code == 201
        assert rv.get_json()["proficiency"] == 80


# ─────────────────────────────────────────────────────────────────────────────
# Assessments
# ─────────────────────────────────────────────────────────────────────────────
class TestAssessments:
    def test_submit_assessment(self, client):
        rv = client.post("/api/students", json={
            "name": "Assmt User", "email": "assmt@test.com"
        })
        sid = rv.get_json()["id"]

        roles_rv = client.get("/api/roles")
        roles = roles_rv.get_json()
        if not roles:
            pytest.skip("No roles seeded")
        skills_rv = client.get(f"/api/roles/{roles[0]['id']}/skills")
        skill_id = skills_rv.get_json()["required_skills"][0]["skill_id"]

        rv2 = client.post(f"/api/students/{sid}/assessments", json={
            "skill_id": skill_id, "score": 75, "max_score": 100
        })
        assert rv2.status_code == 201
        data = rv2.get_json()
        assert data["proficiency"] == 75.0

    def test_invalid_score(self, client):
        rv = client.post("/api/students", json={
            "name": "BadScore", "email": "badscore@test.com"
        })
        sid = rv.get_json()["id"]
        roles_rv = client.get("/api/roles")
        roles = roles_rv.get_json()
        if not roles:
            pytest.skip("No roles")
        skills_rv = client.get(f"/api/roles/{roles[0]['id']}/skills")
        skill_id = skills_rv.get_json()["required_skills"][0]["skill_id"]

        rv2 = client.post(f"/api/students/{sid}/assessments", json={
            "skill_id": skill_id, "score": 120, "max_score": 100
        })
        assert rv2.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# Roles
# ─────────────────────────────────────────────────────────────────────────────
class TestRoles:
    def test_list_roles(self, client):
        rv = client.get("/api/roles")
        assert rv.status_code == 200
        roles = rv.get_json()
        assert isinstance(roles, list)
        assert len(roles) >= 1

    def test_role_skills(self, client):
        rv = client.get("/api/roles")
        roles = rv.get_json()
        if not roles:
            pytest.skip("No roles")
        rv2 = client.get(f"/api/roles/{roles[0]['id']}/skills")
        assert rv2.status_code == 200
        data = rv2.get_json()
        assert "role" in data
        assert "required_skills" in data
        assert len(data["required_skills"]) >= 1

    def test_role_not_found(self, client):
        rv = client.get("/api/roles/99999/skills")
        assert rv.status_code == 404


# ─────────────────────────────────────────────────────────────────────────────
# Full End-to-End Journey
# ─────────────────────────────────────────────────────────────────────────────
class TestEndToEnd:
    def test_full_journey(self, client):
        """
        AC-001 through AC-012 end-to-end:
        Register → Skills → Assessment → Gap Analysis → Recommendations
        → Progress → Reassessment → Dashboard
        """
        # 1. Register student
        rv = client.post("/api/students", json={
            "name": "Rahul E2E", "email": "rahul_e2e@test.com",
            "course": "MCA", "year": 2, "target_career": "Software Developer"
        })
        assert rv.status_code == 201
        sid = rv.get_json()["id"]

        # 2. Get role
        roles = client.get("/api/roles").get_json()
        assert len(roles) > 0
        role_id = roles[0]["id"]
        role_skills_data = client.get(f"/api/roles/{role_id}/skills").get_json()
        req_skills = role_skills_data["required_skills"]
        assert len(req_skills) > 0

        # 3. Add some (low) skills → will have gaps
        for sk in req_skills[:3]:
            rv_s = client.post(f"/api/students/{sid}/skills", json={
                "skill_id": sk["skill_id"], "proficiency": 40
            })
            assert rv_s.status_code == 201

        # 4. Submit an assessment
        rv_a = client.post(f"/api/students/{sid}/assessments", json={
            "skill_id": req_skills[0]["skill_id"],
            "score": 60, "max_score": 100
        })
        assert rv_a.status_code == 201
        assert rv_a.get_json()["proficiency"] == 60.0

        # 5. Add project and certification
        rv_p = client.post(f"/api/students/{sid}/projects", json={
            "title": "REST API Backend Project",
            "description": "Built REST API using Flask and SQLAlchemy"
        })
        assert rv_p.status_code == 201

        rv_c = client.post(f"/api/students/{sid}/certifications", json={
            "name": "AWS Cloud Practitioner", "issuer": "Amazon"
        })
        assert rv_c.status_code == 201

        # 6. Gap analysis (AC-005)
        rv_g = client.post("/api/skill-gap/analyze", json={
            "student_id": sid, "job_role_id": role_id
        })
        assert rv_g.status_code == 200
        gaps = rv_g.get_json()["gaps"]
        assert isinstance(gaps, list)
        assert len(gaps) > 0
        # Verify all gaps have required fields
        for g in gaps:
            assert "severity" in g
            assert g["severity"] in ("LOW", "MEDIUM", "HIGH")

        # 7. Verify gaps are retrievable (AC-006)
        rv_gaps = client.get(f"/api/students/{sid}/gaps?job_role_id={role_id}")
        assert rv_gaps.status_code == 200
        assert isinstance(rv_gaps.get_json(), list)

        # 8. Recommendations (AC-007)
        rv_r = client.get(f"/api/students/{sid}/recommendations?top_k=5")
        assert rv_r.status_code == 200
        recs = rv_r.get_json()
        assert isinstance(recs, list)

        # 9. Record learning progress (AC-009)
        rv_prog = client.post(f"/api/students/{sid}/progress", json={
            "title": "Python for Everybody",
            "status": "in_progress", "completion": 50,
            "skill_id": req_skills[0]["skill_id"]
        })
        assert rv_prog.status_code == 201

        # 10. Reassessment with auto gap refresh (AC-010)
        rv_re = client.post(f"/api/students/{sid}/reassessment", json={
            "skill_id":    req_skills[0]["skill_id"],
            "new_level":   85,
            "job_role_id": role_id
        })
        assert rv_re.status_code == 201
        re_data = rv_re.get_json()
        assert re_data["new_level"] == 85
        assert "updated_gaps" in re_data  # Gap refresh triggered

        # 11. Dashboard (FR-084)
        rv_dash = client.get(f"/api/students/{sid}/dashboard")
        assert rv_dash.status_code == 200
        dash = rv_dash.get_json()
        assert "student" in dash
        assert "current_skills" in dash
        assert "top_gaps" in dash
        assert "active_learning_path" in dash
        assert "progress_summary" in dash
        assert "top_recommendations" in dash
        assert "reassessment_history" in dash


# ─────────────────────────────────────────────────────────────────────────────
# Projects & Certifications
# ─────────────────────────────────────────────────────────────────────────────
class TestProjectsAndCerts:
    def test_add_project(self, client):
        rv = client.post("/api/students", json={
            "name": "ProjUser", "email": "projuser@test.com"
        })
        sid = rv.get_json()["id"]
        rv2 = client.post(f"/api/students/{sid}/projects", json={
            "title": "My Test Project", "description": "A test description"
        })
        assert rv2.status_code == 201

    def test_project_requires_title(self, client):
        rv = client.post("/api/students", json={
            "name": "ProjTitle", "email": "projtitle@test.com"
        })
        sid = rv.get_json()["id"]
        rv2 = client.post(f"/api/students/{sid}/projects", json={})
        assert rv2.status_code == 400

    def test_add_certification(self, client):
        rv = client.post("/api/students", json={
            "name": "CertUser", "email": "certuser@test.com"
        })
        sid = rv.get_json()["id"]
        rv2 = client.post(f"/api/students/{sid}/certifications", json={
            "name": "Python Certified", "issuer": "Coursera"
        })
        assert rv2.status_code == 201


# ─────────────────────────────────────────────────────────────────────────────
# Progress
# ─────────────────────────────────────────────────────────────────────────────
class TestProgress:
    def test_record_progress(self, client):
        rv = client.post("/api/students", json={
            "name": "ProgUser", "email": "proguser@test.com"
        })
        sid = rv.get_json()["id"]
        rv2 = client.post(f"/api/students/{sid}/progress", json={
            "title": "REST API Fundamentals",
            "status": "in_progress", "completion": 30
        })
        assert rv2.status_code == 201

    def test_invalid_completion(self, client):
        rv = client.post("/api/students", json={
            "name": "ProgBad", "email": "progbad@test.com"
        })
        sid = rv.get_json()["id"]
        rv2 = client.post(f"/api/students/{sid}/progress", json={
            "title": "A course", "completion": 150
        })
        assert rv2.status_code == 400

    def test_invalid_status(self, client):
        rv = client.post("/api/students", json={
            "name": "StatusBad", "email": "statusbad@test.com"
        })
        sid = rv.get_json()["id"]
        rv2 = client.post(f"/api/students/{sid}/progress", json={
            "title": "A course", "status": "unknown", "completion": 50
        })
        assert rv2.status_code == 400


# ─────────────────────────────────────────────────────────────────────────────
# Reassessment
# ─────────────────────────────────────────────────────────────────────────────
class TestReassessment:
    def test_reassessment_improves_skill(self, client):
        rv = client.post("/api/students", json={
            "name": "ReTest", "email": "retest@test.com"
        })
        sid = rv.get_json()["id"]
        roles = client.get("/api/roles").get_json()
        if not roles:
            pytest.skip("No roles")
        skills_rv = client.get(f"/api/roles/{roles[0]['id']}/skills")
        skill_id = skills_rv.get_json()["required_skills"][0]["skill_id"]

        # Initial skill at 50
        client.post(f"/api/students/{sid}/skills", json={
            "skill_id": skill_id, "proficiency": 50
        })

        # Reassess to 85
        rv2 = client.post(f"/api/students/{sid}/reassessment", json={
            "skill_id": skill_id, "new_level": 85
        })
        assert rv2.status_code == 201
        data = rv2.get_json()
        assert data["old_level"] == 50.0
        assert data["new_level"] == 85.0
        assert data["improvement"] == 35.0

    def test_reassessment_invalid_level(self, client):
        rv = client.post("/api/students", json={
            "name": "ReInvalid", "email": "reinvalid@test.com"
        })
        sid = rv.get_json()["id"]
        roles = client.get("/api/roles").get_json()
        if not roles:
            pytest.skip("No roles")
        skills_rv = client.get(f"/api/roles/{roles[0]['id']}/skills")
        skill_id = skills_rv.get_json()["required_skills"][0]["skill_id"]
        rv2 = client.post(f"/api/students/{sid}/reassessment", json={
            "skill_id": skill_id, "new_level": 200
        })
        assert rv2.status_code == 400
