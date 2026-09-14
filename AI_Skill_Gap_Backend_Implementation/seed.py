"""
seed.py — Demo seed for local development and presentation.

Creates:
  - Core canonical IT skills (not labeled as ESCO/O*NET)
  - A DEMO Software Developer role with sample requirements
  - Sample learning courses
  - Demo student "Rahul" matching the PRD example use case

IMPORTANT: This DEMO seed is separate from authentic ESCO/O*NET data.
           Run `flask --app app ingest-data` to load real dataset data.
"""
from extensions import db
from models import (
    Student, Skill, StudentSkill, JobRole, JobSkill, Course, CourseSkill
)


def _get_or_create_skill(name: str, category: str) -> "Skill":
    s = Skill.query.filter_by(name=name).first()
    if not s:
        s = Skill(name=name, category=category, source="CANONICAL")
        db.session.add(s)
        db.session.flush()
    return s


def seed_database():
    """Seed demo data. Idempotent — safe to run multiple times."""
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

    # ── DEMO Software Developer role ──────────────────────────────────────
    role = JobRole.query.filter_by(name="Software Developer", source="DEMO").first()
    if not role:
        role = JobRole(
            name="Software Developer", source="DEMO",
            source_identifier="demo-software-developer",
            description=(
                "DEMO role for local development/presentation. "
                "Replace with authentic ESCO data via `flask --app app ingest-data`."
            )
        )
        db.session.add(role)
        db.session.flush()

    demo_requirements = {
        "Java":             (80, 1.0, "essential"),
        "SQL":              (75, 1.0, "essential"),
        "Git":              (70, 1.0, "essential"),
        "REST API":         (75, 1.0, "essential"),
        "Software Testing": (70, 0.9, "essential"),
        "Software Design":  (65, 0.8, "optional"),
        "Docker":           (60, 0.7, "optional"),
    }
    for name, (level, importance, rtype) in demo_requirements.items():
        if not JobSkill.query.filter_by(job_role_id=role.id,
                                        skill_id=skills[name].id).first():
            db.session.add(JobSkill(
                job_role_id=role.id, skill_id=skills[name].id,
                required_level=level, importance=importance,
                relation_type=rtype, source="DEMO"
            ))

    # ── Demo courses ──────────────────────────────────────────────────────
    demo_courses = [
        ("REST API Fundamentals",     "Demo Academy", "REST API",          "https://example.com/rest",    "Intermediate", 4.5),
        ("Software Testing Basics",   "Demo Academy", "Software Testing",  "https://example.com/testing", "Beginner",     4.2),
        ("Docker Fundamentals",       "Demo Academy", "Docker",            "https://example.com/docker",  "Intermediate", 4.6),
        ("Software Design Principles","Demo Academy", "Software Design",   "https://example.com/design",  "Intermediate", 4.4),
        ("Git Essentials",            "Demo Academy", "Git",               "https://example.com/git",     "Beginner",     4.3),
        ("SQL Fundamentals",          "Demo Academy", "SQL",               "https://example.com/sql",     "Beginner",     4.5),
        ("Java for Developers",       "Demo Academy", "Java",              "https://example.com/java",    "Intermediate", 4.1),
        ("Python Programming",        "Demo Academy", "Python",            "https://example.com/python",  "Beginner",     4.8),
    ]
    for title, provider, skill_name, url, difficulty, rating in demo_courses:
        c = Course.query.filter_by(title=title).first()
        if not c:
            c = Course(
                title=title, provider=provider,
                description=f"Learning resource covering {skill_name}.",
                url=url, difficulty_level=difficulty,
                rating=rating, source="DEMO"
            )
            db.session.add(c)
            db.session.flush()
        if skill_name in skills:
            if not CourseSkill.query.filter_by(course_id=c.id,
                                               skill_id=skills[skill_name].id).first():
                db.session.add(CourseSkill(
                    course_id=c.id, skill_id=skills[skill_name].id, relevance=1.0
                ))

    # ── Demo student — Rahul (PRD Example Use Case Section 24) ───────────
    student = Student.query.filter_by(email="rahul@example.com").first()
    if not student:
        student = Student(
            name="Rahul",
            email="rahul@example.com",
            course="MCA",
            year=2,
            target_career="Software Developer"
        )
        db.session.add(student)
        db.session.flush()
        initial_skills = {
            "Java": 75, "SQL": 70, "Git": 60,
            "HTML": 65, "CSS": 65, "Python": 55
        }
        for name, prof in initial_skills.items():
            if name in skills:
                db.session.add(StudentSkill(
                    student_id=student.id,
                    skill_id=skills[name].id,
                    proficiency=prof,
                    evidence_type="demo"
                ))

    db.session.commit()
    print("Demo seed complete. Rahul's profile loaded.")
    print("NOTE: demo role/courses are placeholders. "
          "Run 'flask --app app ingest-data' for real ESCO/Coursera data.")
