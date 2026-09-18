"""
tests/conftest.py — Pytest fixtures for the AI Skill Gap System test suite.

Uses SQLite in-memory database for fast, isolated testing.
"""
import pytest
import pathlib
import tempfile
from app import create_app
from extensions import db as _db
from models import Skill, JobRole, JobSkill, Course, CourseSkill, Student, StudentSkill


from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="session")
def app():
    """Create application with an in-memory SQLite test database."""
    test_config = {
        "TESTING":                  True,
        "SQLALCHEMY_DATABASE_URI":  "sqlite://",
        "SQLALCHEMY_ENGINE_OPTIONS": {
            "poolclass": StaticPool,
            "connect_args": {"check_same_thread": False},
        },
        "WTF_CSRF_ENABLED":         False,
        "UPLOAD_DIR":               str(pathlib.Path(tempfile.gettempdir()) / "skill_gap_test_uploads"),
        "MODEL_PATH":               "ml/models/skill_gap_model.joblib",
    }
    _app = create_app(test_config=test_config)
    with _app.app_context():
        _db.create_all()
        _seed_test_data()
        yield _app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture()
def app_ctx(app):
    """Application context for direct model access."""
    with app.app_context():
        yield app


# ────────────────────────────────────────────────────────────────────────────
# Seed minimal test data
# ────────────────────────────────────────────────────────────────────────────
def _seed_test_data():
    """Insert minimal reference data for testing."""
    # Skills
    skills_data = [
        ("Python", "Programming"),
        ("SQL",    "Database"),
        ("REST API", "Backend"),
        ("Docker", "DevOps"),
        ("Software Testing", "Testing"),
        ("Git",    "Version Control"),
    ]
    skill_objs = {}
    for name, cat in skills_data:
        s = Skill(name=name, category=cat, source="CANONICAL")
        _db.session.add(s)
        _db.session.flush()
        skill_objs[name] = s

    # Job role
    role = JobRole(name="Software Developer", source="ESCO",
                   source_identifier="http://data.europa.eu/esco/occupation/f2b15a0e")
    _db.session.add(role)
    _db.session.flush()

    # Role requirements
    req = {"Python": 80, "SQL": 75, "REST API": 75, "Docker": 60, "Software Testing": 70}
    for sname, level in req.items():
        _db.session.add(JobSkill(
            job_role_id=role.id, skill_id=skill_objs[sname].id,
            required_level=level, importance=1.0, relation_type="essential", source="ESCO"
        ))

    # Courses
    courses_data = [
        ("Python for Everybody",    "Coursera", "Learn Python", "https://coursera.org/1", "Beginner",  4.8, "Python"),
        ("REST API Fundamentals",   "Udemy",    "Build REST APIs", "https://udemy.com/1", "Intermediate", 4.5, "REST API"),
        ("Docker Deep Dive",        "Pluralsight", "Master Docker", "https://ps.com/1",   "Advanced",  4.7, "Docker"),
        ("SQL for Data Science",    "Coursera", "Learn SQL", "https://coursera.org/2",   "Beginner",  4.6, "SQL"),
        ("Software Testing Basics", "Udemy",    "Learn testing", "https://udemy.com/2",  "Beginner",  4.2, "Software Testing"),
    ]
    for title, prov, desc, url, diff, rating, skill_name in courses_data:
        c = Course(title=title, provider=prov, description=desc, url=url,
                   difficulty_level=diff, rating=rating, source="Test")
        _db.session.add(c)
        _db.session.flush()
        _db.session.add(CourseSkill(
            course_id=c.id, skill_id=skill_objs[skill_name].id, relevance=1.0
        ))

    _db.session.commit()
