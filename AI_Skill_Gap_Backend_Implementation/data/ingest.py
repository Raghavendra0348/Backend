"""
data/ingest.py — ETL pipeline for ESCO v1.2.1, O*NET, Coursera, and Student datasets.

Run via Flask CLI:
    flask --app app ingest-data

This populates:
    - job_roles      (from ESCO)
    - skills         (canonical vocabulary from ESCO + IT-specific additions)
    - job_skills     (ESCO occupation-skill relations for IT roles)
    - courses        (from Coursera.csv in the Dataset archive)
    - course_skills  (mapped from Coursera "Skills" column)
    - students       (sample from Indian names student dataset)
    - student_skills (from student dataset "technical_skills" + "rating" columns)
"""
import csv
import io
import os
import re
import zipfile
from pathlib import Path
from flask import current_app

from extensions import db
from models import (
    JobRole, Skill, JobSkill, Course, CourseSkill, Student, StudentSkill
)

# ─────────────────────────────────────────────────────────────────────────────
# IT Occupation URIs to ingest from ESCO (carefully selected for IT students)
# ─────────────────────────────────────────────────────────────────────────────
ESCO_IT_OCCUPATION_URIS = {
    "software developer":
        "http://data.europa.eu/esco/occupation/f2b15a0e-e65a-438a-affb-29b9d50b77d1",
    "data scientist":
        "http://data.europa.eu/esco/occupation/258e46f9-0075-4a2e-adae-1ff0477e0f30",
    "web developer":
        "http://data.europa.eu/esco/occupation/c40a2919-48a9-40ea-b506-1f34f693496d",
    "database administrator":
        "http://data.europa.eu/esco/occupation/8c57af09-719c-42b3-be40-6ed4946236cc",
    "ICT system analyst":
        "http://data.europa.eu/esco/occupation/a6a0b60f-08da-4faa-bf54-942987efb471",
    "cloud DevOps engineer":
        "http://data.europa.eu/esco/occupation/cc867bee-ab5c-427f-9244-f7a204d9574b",
}

# Skill category inference from ESCO skill labels (keyword → category)
SKILL_CATEGORY_MAP = [
    (["python", "java", "javascript", "c++", "c#", "sql", "r ", "php",
      "ruby", "scala", "go ", "kotlin", "swift", "typescript", "html", "css"],
     "Programming"),
    (["machine learning", "deep learning", "neural network", "tensorflow",
      "pytorch", "scikit", "nlp", "natural language", "computer vision",
      "reinforcement learning", "ai ", "artificial intelligence"],
     "Artificial Intelligence"),
    (["database", "sql", "nosql", "mongodb", "postgresql", "mysql",
      "oracle", "sqlite", "redis", "data model"],
     "Database"),
    (["docker", "kubernetes", "devops", "ci/cd", "jenkins", "git",
      "ansible", "terraform", "cloud", "aws", "azure", "gcp",
      "linux", "unix", "shell", "bash", "deployment"],
     "DevOps"),
    (["rest", "api", "microservice", "web service", "http", "json",
      "xml", "graphql", "soap", "backend"],
     "Backend"),
    (["test", "debugging", "debug", "quality assurance", "qa ",
      "unit test", "selenium", "junit"],
     "Testing"),
    (["project management", "agile", "scrum", "kanban", "leadership",
      "communication", "teamwork", "problem solving"],
     "Soft Skills"),
    (["statistics", "mathematics", "linear algebra", "calculus",
      "data analysis", "pandas", "numpy", "visualization"],
     "Data Science"),
    (["security", "cryptography", "firewall", "vulnerability",
      "penetration", "cybersecurity", "ethical hack"],
     "Security"),
    (["software design", "architecture", "design pattern", "uml",
      "object-oriented", "oop", "solid"],
     "Software Engineering"),
]


def infer_skill_category(skill_label: str) -> str:
    lower = skill_label.lower()
    for keywords, category in SKILL_CATEGORY_MAP:
        if any(kw in lower for kw in keywords):
            return category
    return "General"


def get_or_create_skill(name: str, source_uri: str = None, category: str = None) -> Skill:
    """Return existing Skill or create a new one. Normalizes name to title-case."""
    name = name.strip()
    s = Skill.query.filter(db.func.lower(Skill.name) == name.lower()).first()
    if not s:
        cat = category or infer_skill_category(name)
        s = Skill(
            name=name, category=cat,
            source="ESCO" if source_uri else "CANONICAL",
            source_identifier=source_uri
        )
        db.session.add(s)
        db.session.flush()
    return s


# ─────────────────────────────────────────────────────────────────────────────
# ESCO Ingestion
# ─────────────────────────────────────────────────────────────────────────────
def ingest_esco(esco_dir: str) -> dict:
    """
    Ingest IT occupations and their skills from ESCO v1.2.1 CSV files.
    Returns a summary dict of counts.
    """
    esco_path = Path(esco_dir)
    occ_file = esco_path / "occupations_en.csv"
    rel_file = esco_path / "occupationSkillRelations_en.csv"

    if not occ_file.exists() or not rel_file.exists():
        print(f"  [ESCO] WARNING: CSV files not found at {esco_dir}. Skipping ESCO ingestion.")
        return {"roles": 0, "skills": 0, "job_skills": 0}

    print(f"  [ESCO] Loading occupations from {occ_file}...")

    # Build URI → occupation data map for IT roles
    occ_map = {}
    with open(occ_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["conceptUri"] in ESCO_IT_OCCUPATION_URIS.values():
                occ_map[row["conceptUri"]] = {
                    "name": row["preferredLabel"],
                    "isco_group": row.get("iscoGroup", ""),
                    "description": row.get("description", "")[:500],
                }

    # Create JobRole records
    roles_created = 0
    role_id_map = {}  # URI → db row id
    for uri, data in occ_map.items():
        existing = JobRole.query.filter_by(source="ESCO", source_identifier=uri).first()
        if not existing:
            role = JobRole(
                name=data["name"],
                source="ESCO",
                source_identifier=uri,
                description=data.get("description", ""),
                isco_group=data.get("isco_group", "")
            )
            db.session.add(role)
            db.session.flush()
            role_id_map[uri] = role.id
            roles_created += 1
        else:
            role_id_map[uri] = existing.id
    print(f"  [ESCO] {roles_created} new JobRole records (IT occupations).")

    # Ingest occupation-skill relations
    print(f"  [ESCO] Loading skill relations from {rel_file}...")
    skills_created = 0
    job_skills_created = 0

    with open(rel_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            occ_uri = row["occupationUri"]
            if occ_uri not in role_id_map:
                continue

            skill_label = row["skillLabel"].strip()
            skill_uri = row["skillUri"]
            relation_type = row["relationType"]   # essential | optional

            skill = get_or_create_skill(skill_label, skill_uri)
            if skill.id not in [s.id for s in [skill]]:
                skills_created += 1

            # required_level and importance: essential = 75–80, optional = 55–65
            required_level = 78.0 if relation_type == "essential" else 60.0
            importance = 1.0 if relation_type == "essential" else 0.7

            existing_js = JobSkill.query.filter_by(
                job_role_id=role_id_map[occ_uri], skill_id=skill.id
            ).first()
            if not existing_js:
                db.session.add(JobSkill(
                    job_role_id=role_id_map[occ_uri],
                    skill_id=skill.id,
                    required_level=required_level,
                    importance=importance,
                    relation_type=relation_type,
                    source="ESCO"
                ))
                job_skills_created += 1

    db.session.commit()
    # Count new skills (approximate after flush)
    skills_created = Skill.query.filter_by(source="ESCO").count()
    print(f"  [ESCO] {skills_created} ESCO skills total, {job_skills_created} new JobSkill records.")
    return {"roles": roles_created, "skills": skills_created, "job_skills": job_skills_created}


# ─────────────────────────────────────────────────────────────────────────────
# Coursera Dataset Ingestion
# ─────────────────────────────────────────────────────────────────────────────

# IT-relevant Coursera skills to filter and map to canonical skills
IT_SKILL_KEYWORDS = {
    "python", "java", "javascript", "sql", "machine learning", "deep learning",
    "data science", "web development", "docker", "kubernetes", "devops",
    "cloud", "aws", "azure", "git", "database", "nosql", "mongodb",
    "rest", "api", "html", "css", "react", "node", "angular", "flask",
    "django", "spring", "testing", "agile", "scrum", "linux", "security",
    "nlp", "tensorflow", "pytorch", "pandas", "numpy", "r programming",
    "statistics", "data analysis", "big data", "spark", "hadoop",
    "c++", "c#", "kotlin", "swift", "typescript", "ruby", "scala",
    "software design", "object-oriented", "algorithms", "data structures",
    "cryptography", "cybersecurity", "ethical hacking",
}


def _coursera_skill_to_canonical(raw_skill: str) -> str | None:
    """Normalize a Coursera skill tag to a canonical-ish label."""
    s = raw_skill.strip().lower()
    if not s:
        return None
    # Filter to IT skills
    if not any(kw in s for kw in IT_SKILL_KEYWORDS):
        return None
    # Normalize common variations
    norm = {
        "python programming": "Python", "python 3": "Python",
        "java programming": "Java", "javascript basics": "JavaScript",
        "sql programming": "SQL", "mysql": "MySQL",
        "machine learning": "Machine Learning", "ml": "Machine Learning",
        "deep learning": "Deep Learning", "neural networks": "Deep Learning",
        "web development": "Web Development", "web design": "Web Development",
        "docker": "Docker", "kubernetes": "Kubernetes",
        "cloud computing": "Cloud Computing", "aws": "AWS",
        "git": "Git", "github": "Git",
        "rest api": "REST API", "restful api": "REST API",
        "software testing": "Software Testing", "unit testing": "Software Testing",
        "natural language processing": "NLP", "nlp": "NLP",
        "data analysis": "Data Analysis",
        "data visualization": "Data Visualization",
        "software design": "Software Design",
        "algorithms": "Algorithms & Data Structures",
        "data structures": "Algorithms & Data Structures",
    }
    return norm.get(s, raw_skill.strip().title())


def ingest_coursera(coursera_zip: str) -> dict:
    """
    Ingest Coursera courses from Dataset/archive (1).zip → Coursera.csv.
    Only ingests IT-relevant courses (based on Skills column keywords).
    """
    if not Path(coursera_zip).exists():
        print(f"  [Coursera] WARNING: {coursera_zip} not found. Skipping.")
        return {"courses": 0, "course_skills": 0}

    print(f"  [Coursera] Loading courses from {coursera_zip}...")

    courses_created = 0
    course_skills_created = 0

    with zipfile.ZipFile(coursera_zip) as z:
        with z.open("Coursera.csv") as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"))
            for row in reader:
                raw_skills_str = row.get("Skills", "")
                if not raw_skills_str:
                    continue

                # Parse skills field (semicolon or comma separated)
                raw_skills = [
                    s.strip() for s in re.split(r"[;,]", raw_skills_str) if s.strip()
                ]
                canonical_skills = [
                    _coursera_skill_to_canonical(s) for s in raw_skills
                ]
                canonical_skills = [s for s in canonical_skills if s]

                if not canonical_skills:
                    continue  # Skip non-IT courses

                title = (row.get("Course Name") or "").strip()
                provider = (row.get("University") or "Coursera").strip()
                url = (row.get("Course URL") or "").strip()
                description = (row.get("Course Description") or "").strip()[:600]
                difficulty = (row.get("Difficulty Level") or "").strip()
                try:
                    rating = float(row.get("Course Rating") or 0)
                except (ValueError, TypeError):
                    rating = 0.0

                if not title:
                    continue

                # Upsert course (avoid duplicates by title+provider)
                course = Course.query.filter_by(title=title, provider=provider).first()
                if not course:
                    course = Course(
                        title=title, provider=provider, url=url,
                        description=description, difficulty_level=difficulty,
                        rating=rating, source="Coursera"
                    )
                    db.session.add(course)
                    db.session.flush()
                    courses_created += 1

                # Map canonical skills to CourseSkill
                for skill_name in canonical_skills:
                    skill = get_or_create_skill(skill_name)
                    existing = CourseSkill.query.filter_by(
                        course_id=course.id, skill_id=skill.id
                    ).first()
                    if not existing:
                        db.session.add(CourseSkill(
                            course_id=course.id, skill_id=skill.id, relevance=0.9
                        ))
                        course_skills_created += 1

    db.session.commit()
    print(f"  [Coursera] {courses_created} new courses, {course_skills_created} new CourseSkill records.")
    return {"courses": courses_created, "course_skills": course_skills_created}


# ─────────────────────────────────────────────────────────────────────────────
# Student Dataset Ingestion
# ─────────────────────────────────────────────────────────────────────────────
def ingest_students(student_xlsx: str, max_students: int = 20) -> dict:
    """
    Ingest sample student profiles and self-reported skills from
    Final_Updated_DMA_DATASET_Indian_Names (1).xlsx.
    """
    if not Path(student_xlsx).exists():
        print(f"  [Students] WARNING: {student_xlsx} not found. Skipping.")
        return {"students": 0, "student_skills": 0}

    print(f"  [Students] Loading student profiles from {student_xlsx}...")

    try:
        import openpyxl
    except ImportError:
        print("  [Students] openpyxl not installed. Skipping student ingestion.")
        return {"students": 0, "student_skills": 0}

    wb = openpyxl.load_workbook(student_xlsx, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    header = [str(h).strip() if h else "" for h in rows[0]]

    students_created = 0
    student_skills_created = 0

    for raw in rows[1: max_students + 1]:
        row = dict(zip(header, raw))
        name = str(row.get("name") or "").strip()
        email = str(row.get("email_id") or "").strip()
        if not name or not email:
            continue

        # Skip if email already exists
        if Student.query.filter_by(email=email).first():
            continue

        year_str = str(row.get("year") or "").strip()
        year_map = {"1st Year": 1, "2nd Year": 2, "3rd Year": 3, "4th Year": 4}
        year = year_map.get(year_str, 1)
        course = str(row.get("current_course") or "MCA").strip()
        aspiration = str(row.get("job_role_aspiration") or "").strip()

        s = Student(
            name=name, email=email,
            course=course, year=year, target_career=aspiration
        )
        db.session.add(s)
        db.session.flush()
        students_created += 1

        # Parse technical_skills + rating
        skills_raw = str(row.get("technical_skills") or "").strip()
        rating_raw = str(row.get("rating") or "3").strip()
        try:
            rating_value = float(rating_raw) * 20  # Convert 1-5 scale to 0-100
        except (ValueError, TypeError):
            rating_value = 60.0

        if skills_raw:
            for sk_name in re.split(r"[;,]", skills_raw):
                sk_name = sk_name.strip()
                if not sk_name:
                    continue
                skill = get_or_create_skill(sk_name)
                existing = StudentSkill.query.filter_by(
                    student_id=s.id, skill_id=skill.id
                ).first()
                if not existing:
                    db.session.add(StudentSkill(
                        student_id=s.id, skill_id=skill.id,
                        proficiency=min(rating_value, 100),
                        evidence_type="self_reported",
                        confidence=0.9
                    ))
                    student_skills_created += 1

        # Parse programming_languages
        langs_raw = str(row.get("programming_languages") or "").strip()
        if langs_raw:
            for lang in re.split(r"[;,]", langs_raw):
                lang = lang.strip()
                if not lang:
                    continue
                skill = get_or_create_skill(lang, category="Programming")
                existing = StudentSkill.query.filter_by(
                    student_id=s.id, skill_id=skill.id
                ).first()
                if not existing:
                    db.session.add(StudentSkill(
                        student_id=s.id, skill_id=skill.id,
                        proficiency=min(rating_value, 100),
                        evidence_type="self_reported",
                        confidence=0.9
                    ))
                    student_skills_created += 1

    db.session.commit()
    wb.close()
    print(f"  [Students] {students_created} new students, {student_skills_created} new StudentSkill records.")
    return {"students": students_created, "student_skills": student_skills_created}


# ─────────────────────────────────────────────────────────────────────────────
# Master ingestion function
# ─────────────────────────────────────────────────────────────────────────────
def run_ingestion() -> dict:
    """
    Run the full ingestion pipeline in order:
    1. ESCO IT occupations and skills
    2. Coursera courses
    3. Student profiles
    """
    cfg = current_app.config
    print("\n=== Starting Data Ingestion Pipeline ===")

    summary = {}

    print("\n[1/3] ESCO v1.2.1 Ingestion")
    summary["esco"] = ingest_esco(cfg["ESCO_DATA_DIR"])

    print("\n[2/3] Coursera Dataset Ingestion")
    summary["coursera"] = ingest_coursera(cfg["COURSERA_ZIP"])

    print("\n[3/3] Student Dataset Ingestion")
    summary["students"] = ingest_students(cfg["STUDENT_DATASET_XLSX"])

    print("\n=== Ingestion Complete ===")
    print(f"  ESCO:     {summary['esco']['roles']} IT roles, "
          f"{summary['esco']['job_skills']} job-skill mappings")
    print(f"  Coursera: {summary['coursera']['courses']} courses, "
          f"{summary['coursera']['course_skills']} course-skill mappings")
    print(f"  Students: {summary['students']['students']} students, "
          f"{summary['students']['student_skills']} student skills")

    return summary
