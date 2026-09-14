"""
seed.py — Populates baseline canonical IT skill taxonomy into the database.
Authentic ESCO occupations and Coursera courses are loaded via `flask --app app ingest-data`.
"""
from extensions import db
from models import Skill


def _get_or_create_skill(name: str, category: str) -> "Skill":
    s = Skill.query.filter_by(name=name).first()
    if not s:
        s = Skill(name=name, category=category, source="CANONICAL")
        db.session.add(s)
        db.session.flush()
    return s


def seed_database():
    """Seed core canonical IT skills. Idempotent — safe to run multiple times."""
    skill_defs = {
        "Java":                ("Programming",),
        "Python":              ("Programming",),
        "JavaScript":          ("Programming",),
        "SQL":                 ("Database",),
        "MongoDB":             ("Database",),
        "Git":                 ("Version Control",),
        "REST API":            ("Backend",),
        "Software Testing":    ("Testing",),
        "Software Design":     ("Software Engineering",),
        "Docker":              ("DevOps",),
        "Kubernetes":          ("DevOps",),
        "Machine Learning":    ("Artificial Intelligence",),
        "Data Analysis":       ("Data Science",),
        "HTML":                ("Frontend",),
        "CSS":                 ("Frontend",),
    }
    skills = {name: _get_or_create_skill(name, cat[0]) for name, cat in skill_defs.items()}
    db.session.commit()
    print(f"Canonical skills seeded ({len(skills)} skills).")
