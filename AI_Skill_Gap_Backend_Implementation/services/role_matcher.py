"""
services/role_matcher.py — Job Role Match Score computation.

Computes how well a student's current skills match each job role's requirements.

Algorithm (weighted coverage):
    match_score = Σ(min(student_lvl, required_lvl) × importance)
                / Σ(required_lvl × importance) × 100

    - Weighted by importance (essential skills weight more than optional)
    - Per-category breakdown for detailed insight
    - Skills the student hasn't listed count as 0
"""
from __future__ import annotations

from extensions import db
from models import JobRole, JobSkill, Skill, StudentSkill


def compute_role_match(student_id: int, job_role_id: int | None = None) -> list[dict]:
    """
    Compute match score for a student against all roles (or one specific role).

    Returns a list of match dicts, sorted by match_score descending.
    """
    # Build student skill map: {skill_id: proficiency}
    ss_rows = StudentSkill.query.filter_by(student_id=student_id).all()
    student_skills: dict[int, float] = {
        ss.skill_id: float(ss.proficiency) for ss in ss_rows
    }

    # Determine which roles to evaluate
    if job_role_id:
        roles = [db.session.get(JobRole, job_role_id)]
        roles = [r for r in roles if r]
    else:
        roles = JobRole.query.order_by(JobRole.name).all()

    results = []

    for role in roles:
        # Fetch all required skills for this role
        js_rows = (
            db.session.query(JobSkill, Skill)
            .join(Skill, Skill.id == JobSkill.skill_id)
            .filter(JobSkill.job_role_id == role.id)
            .all()
        )

        if not js_rows:
            continue

        # Weighted sums
        weighted_achieved = 0.0
        weighted_required = 0.0
        covered_skills     = 0
        missing_skills     = []
        by_category: dict[str, dict] = {}

        for js, skill in js_rows:
            req   = float(js.required_level) if js.required_level else 50.0
            imp   = float(js.importance)     if js.importance     else 1.0
            curr  = student_skills.get(skill.id, 0.0)

            achieved = min(curr, req) * imp
            required = req * imp

            weighted_achieved += achieved
            weighted_required += required

            if curr > 0:
                covered_skills += 1
            else:
                missing_skills.append(skill.name)

            # Category breakdown
            cat = skill.category or "General"
            if cat not in by_category:
                by_category[cat] = {"achieved": 0.0, "required": 0.0}
            by_category[cat]["achieved"] += achieved
            by_category[cat]["required"] += required

        match_score = round(
            (weighted_achieved / weighted_required * 100) if weighted_required > 0 else 0.0,
            2
        )

        # Category-level match percentages
        category_scores = {
            cat: round(
                (v["achieved"] / v["required"] * 100) if v["required"] > 0 else 0.0, 2
            )
            for cat, v in by_category.items()
        }

        results.append({
            "role_id":           role.id,
            "role":              role.name,
            "onet_code":         role.onet_code,
            "match_score":       match_score,
            "ready":             match_score >= 80.0,
            "skill_coverage":    covered_skills,
            "total_skills":      len(js_rows),
            "top_missing":       missing_skills[:5],     # top 5 skills not yet started
            "by_category":       category_scores,
            "verdict": (
                "Job-ready 🎯"    if match_score >= 80 else
                "Almost there 💪" if match_score >= 60 else
                "In progress 📚"  if match_score >= 40 else
                "Just starting 🚀"
            ),
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results
