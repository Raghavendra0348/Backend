"""
services/learning_path.py — Personalized Learning Path generator.

Generates a structured, phased learning roadmap for a student targeting a specific job role.

Algorithm:
  1. Run (or fetch) gap analysis for the target role
  2. Sort gaps by priority (HIGH first, then by priority_score)
  3. For each gap skill, find best matching courses (by difficulty level + TF-IDF relevance)
  4. Group into phases:
       Phase 1 — Critical (HIGH severity gaps)
       Phase 2 — Moderate (MEDIUM severity gaps)
       Phase 3 — Polish   (LOW severity gaps)
  5. Deduplicate: one course can cover multiple skills
  6. Assign estimated hours per course based on difficulty
  7. Persist to LearningPath + LearningPathStep tables

Usage:
    from services.learning_path import generate_learning_path
    path = generate_learning_path(student_id=1, job_role_id=2)
"""
from __future__ import annotations

from extensions import db
from models import (
    Course, CourseSkill, JobRole, LearningPath,
    LearningPathStep, Skill, SkillGap, StudentSkill,
)

# Estimated study hours by difficulty
HOURS_BY_DIFFICULTY = {
    "beginner":     20,
    "intermediate": 35,
    "advanced":     50,
    None:           25,
}

PHASE_LABELS = {
    "HIGH":   ("Phase 1 — Critical Skills",  "Fill the most critical skill gaps first"),
    "MEDIUM": ("Phase 2 — Core Development", "Build up moderate gaps to become competitive"),
    "LOW":    ("Phase 3 — Final Polish",      "Fine-tune remaining minor gaps"),
}


def _best_courses_for_skill(skill_id: int, limit: int = 2) -> list[Course]:
    """Find the most relevant courses for a given skill, ordered by relevance then rating."""
    rows = (
        db.session.query(Course, CourseSkill.relevance)
        .join(CourseSkill, CourseSkill.course_id == Course.id)
        .filter(CourseSkill.skill_id == skill_id)
        .order_by(CourseSkill.relevance.desc(), Course.rating.desc())
        .limit(limit)
        .all()
    )
    return [r[0] for r in rows]


def _estimated_hours(course: Course) -> int:
    diff = (course.difficulty_level or "").lower().strip()
    for key in HOURS_BY_DIFFICULTY:
        if key and key in diff:
            return HOURS_BY_DIFFICULTY[key]
    return HOURS_BY_DIFFICULTY[None]


def generate_learning_path(student_id: int, job_role_id: int) -> dict:
    """
    Generate (or regenerate) a personalized learning path.
    Persists to DB and returns the structured path as a dict.
    """
    role = db.session.get(JobRole, job_role_id)
    if not role:
        return {"error": f"Job role {job_role_id} not found"}

    # ── Fetch gaps sorted by severity + priority ──────────────────────────────
    severity_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    gaps = (
        db.session.query(SkillGap, Skill)
        .join(Skill, Skill.id == SkillGap.skill_id)
        .filter(
            SkillGap.student_id == student_id,
            SkillGap.job_role_id == job_role_id,
            SkillGap.gap_value > 0,
        )
        .all()
    )

    if not gaps:
        return {
            "message":    "No gaps found. Run gap analysis first.",
            "job_role":   role.name,
            "phases":     [],
        }

    gaps_sorted = sorted(
        gaps,
        key=lambda x: (severity_order.get(x[0].severity, 3), -x[0].priority_score)
    )

    # ── Group by severity into phases ─────────────────────────────────────────
    phases_raw: dict[str, list] = {"HIGH": [], "MEDIUM": [], "LOW": []}
    used_course_ids: set[int] = set()
    step_order = 1

    for gap, skill in gaps_sorted:
        sev = gap.severity
        courses = _best_courses_for_skill(skill.id, limit=2)

        new_courses = [c for c in courses if c.id not in used_course_ids]
        if not new_courses and courses:
            # Allow re-use if no alternatives (multi-skill course)
            new_courses = [courses[0]]

        for course in new_courses[:1]:  # Max 1 course per skill in path
            used_course_ids.add(course.id)
            phases_raw[sev].append({
                "order":          step_order,
                "skill_id":       skill.id,
                "skill":          skill.name,
                "skill_gap":      round(gap.gap_percent, 1),
                "severity":       sev,
                "course_id":      course.id,
                "course":         course.title,
                "provider":       course.provider,
                "difficulty":     course.difficulty_level,
                "rating":         course.rating,
                "url":            course.url,
                "estimated_hours": _estimated_hours(course),
            })
            step_order += 1

    # ── Compute totals ─────────────────────────────────────────────────────────
    all_steps = phases_raw["HIGH"] + phases_raw["MEDIUM"] + phases_raw["LOW"]
    total_hours   = sum(s["estimated_hours"] for s in all_steps)
    total_courses = len(all_steps)

    # ── Compute match score for context ──────────────────────────────────────
    from services.role_matcher import compute_role_match
    match_results = compute_role_match(student_id, job_role_id)
    match_score   = match_results[0]["match_score"] if match_results else 0.0

    # ── Persist to DB ─────────────────────────────────────────────────────────
    # Delete old path for this student+role
    old_path = LearningPath.query.filter_by(
        student_id=student_id, job_role_id=job_role_id
    ).first()
    if old_path:
        LearningPathStep.query.filter_by(path_id=old_path.id).delete()
        db.session.delete(old_path)
        db.session.flush()

    path = LearningPath(
        student_id=student_id,
        job_role_id=job_role_id,
        total_courses=total_courses,
        total_hours=total_hours,
        match_score_at_generation=round(match_score, 2),
    )
    db.session.add(path)
    db.session.flush()

    for step_dict in all_steps:
        step = LearningPathStep(
            path_id=path.id,
            step_order=step_dict["order"],
            course_id=step_dict["course_id"],
            skill_id=step_dict["skill_id"],
            phase=step_dict["severity"],
            estimated_hours=step_dict["estimated_hours"],
        )
        db.session.add(step)

    db.session.commit()

    # ── Build response ─────────────────────────────────────────────────────────
    phases_out = []
    for sev in ("HIGH", "MEDIUM", "LOW"):
        steps = phases_raw[sev]
        if not steps:
            continue
        label, desc = PHASE_LABELS[sev]
        phases_out.append({
            "phase":       {"HIGH": 1, "MEDIUM": 2, "LOW": 3}[sev],
            "name":        label,
            "description": desc,
            "severity":    sev,
            "courses":     steps,
            "phase_hours": sum(s["estimated_hours"] for s in steps),
        })

    return {
        "path_id":           path.id,
        "job_role":          role.name,
        "job_role_id":       role.id,
        "match_score":       match_score,
        "total_courses":     total_courses,
        "estimated_hours":   total_hours,
        "estimated_weeks":   round(total_hours / 10),   # ~10 hrs/week
        "phases":            phases_out,
        "generated_at":      path.created_at.isoformat() if path.created_at else None,
    }


def get_learning_path(student_id: int, job_role_id: int) -> dict | None:
    """Retrieve a saved learning path from DB."""
    path = LearningPath.query.filter_by(
        student_id=student_id, job_role_id=job_role_id
    ).first()
    if not path:
        return None

    steps = (
        db.session.query(LearningPathStep, Course, Skill)
        .join(Course, Course.id == LearningPathStep.course_id)
        .join(Skill,  Skill.id  == LearningPathStep.skill_id)
        .filter(LearningPathStep.path_id == path.id)
        .order_by(LearningPathStep.step_order)
        .all()
    )

    role = db.session.get(JobRole, path.job_role_id)

    phases_dict: dict[str, list] = {"HIGH": [], "MEDIUM": [], "LOW": []}
    for step, course, skill in steps:
        phases_dict[step.phase].append({
            "order":           step.step_order,
            "skill":           skill.name,
            "course":          course.title,
            "provider":        course.provider,
            "difficulty":      course.difficulty_level,
            "rating":          course.rating,
            "url":             course.url,
            "estimated_hours": step.estimated_hours,
        })

    phases_out = []
    for sev in ("HIGH", "MEDIUM", "LOW"):
        items = phases_dict[sev]
        if not items:
            continue
        label, desc = PHASE_LABELS[sev]
        phases_out.append({
            "phase":       {"HIGH": 1, "MEDIUM": 2, "LOW": 3}[sev],
            "name":        label,
            "description": desc,
            "severity":    sev,
            "courses":     items,
            "phase_hours": sum(s["estimated_hours"] for s in items),
        })

    return {
        "path_id":         path.id,
        "job_role":        role.name if role else "Unknown",
        "job_role_id":     path.job_role_id,
        "match_score":     path.match_score_at_generation,
        "total_courses":   path.total_courses,
        "estimated_hours": path.total_hours,
        "estimated_weeks": round(path.total_hours / 10),
        "phases":          phases_out,
        "generated_at":    path.created_at.isoformat() if path.created_at else None,
    }
