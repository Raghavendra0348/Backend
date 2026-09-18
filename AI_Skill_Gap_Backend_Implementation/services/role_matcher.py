"""
services/role_matcher.py — Job Role Match Score & Readiness computation.

Algorithm (weighted coverage):
    readiness_score = Σ(min(user_level, required_level) × weight)
                    / Σ(required_level × weight) × 100

Features:
    - Weighted coverage across essential and optional skills
    - Profile verification confidence score (assessed vs resume vs self-reported)
    - Full explainability for match verdict and evidence breakdown
"""
from __future__ import annotations

from extensions import db
from models import JobRole, JobSkill, Skill, StudentSkill


def _get_skill_evidence_confidence(evidence_type: str | None, current_level: float) -> tuple[float, str]:
    """
    Return (confidence_weight, category_key) for a skill's evidence.
    Weights: verified (1.0), resume (0.6), self-reported (0.3), unacquired (0.0).
    """
    if current_level <= 0 or not evidence_type:
        return 0.0, "unacquired"

    ev = evidence_type.lower()
    if ev in ("assessment", "certified", "certification", "reassessment"):
        return 1.0, "verified"
    if ev == "resume":
        return 0.6, "resume"
    if ev == "self_reported":
        return 0.3, "self_reported"
    return 0.3, "self_reported"


def compute_role_match(student_id: int, job_role_id: int | None = None) -> list[dict]:
    """
    Compute role readiness score and profile verification confidence for a student
    against all roles (or one specific role).
    """
    # Build student skill map: {skill_id: (proficiency, evidence_type)}
    ss_rows = StudentSkill.query.filter_by(student_id=student_id).all()
    student_skills: dict[int, tuple[float, str]] = {
        ss.skill_id: (float(ss.proficiency), ss.evidence_type or "self_reported")
        for ss in ss_rows
    }

    # Determine which roles to evaluate
    if job_role_id:
        roles = [db.session.get(JobRole, job_role_id)]
        roles = [r for r in roles if r]
    else:
        roles = JobRole.query.order_by(JobRole.name).all()

    results = []

    for role in roles:
        js_rows = (
            db.session.query(JobSkill, Skill)
            .join(Skill, Skill.id == JobSkill.skill_id)
            .filter(JobSkill.job_role_id == role.id)
            .all()
        )

        if not js_rows:
            continue

        weighted_achieved = 0.0
        weighted_required = 0.0
        covered_skills = 0
        missing_skills = []
        by_category: dict[str, dict] = {}

        total_importance = 0.0
        weighted_evidence_conf = 0.0
        verification_counts = {
            "verified": 0,
            "resume": 0,
            "self_reported": 0,
            "unacquired": 0,
        }

        for js, skill in js_rows:
            req = float(js.required_level) if js.required_level else 50.0
            imp = float(js.importance) if js.importance else 1.0
            total_importance += imp

            from services.skill_normalizer import get_equivalent_skill_ids
            eq_ids = get_equivalent_skill_ids(skill.id)

            curr = 0.0
            evidence_type = "unacquired"
            for eid in eq_ids:
                if eid in student_skills:
                    p, ev = student_skills[eid]
                    if p > curr:
                        curr = p
                        evidence_type = ev

            achieved = min(curr, req) * imp
            required = req * imp

            weighted_achieved += achieved
            weighted_required += required

            # Evidence confidence
            ev_conf_weight, ev_cat = _get_skill_evidence_confidence(evidence_type, curr)
            weighted_evidence_conf += ev_conf_weight * imp
            verification_counts[ev_cat] += 1

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

        verification_confidence = round(
            (weighted_evidence_conf / total_importance * 100) if total_importance > 0 else 0.0,
            1
        )

        category_scores = {
            cat: round(
                (v["achieved"] / v["required"] * 100) if v["required"] > 0 else 0.0, 2
            )
            for cat, v in by_category.items()
        }

        # Explainable verdict
        verdict = (
            "Job-ready 🎯" if match_score >= 80 else
            "Almost there 💪" if match_score >= 60 else
            "In progress 📚" if match_score >= 40 else
            "Just starting 🚀"
        )

        explanation = (
            f"{verdict} ({match_score}% readiness): {covered_skills}/{len(js_rows)} required skills "
            f"addressed. Profile verification confidence is {verification_confidence}% "
            f"({verification_counts['verified']} verified, {verification_counts['resume']} from resume, "
            f"{verification_counts['self_reported']} self-reported, {verification_counts['unacquired']} missing)."
        )

        results.append({
            "role_id": role.id,
            "role": role.name,
            "onet_code": role.onet_code,
            "match_score": match_score,
            "ready": match_score >= 80.0,
            "skill_coverage": covered_skills,
            "total_skills": len(js_rows),
            "top_missing": missing_skills[:5],
            "by_category": category_scores,
            "verification_confidence": verification_confidence,
            "verification_breakdown": verification_counts,
            "explanation": explanation,
            "verdict": verdict,
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results


class RoleMatcherService:
    @staticmethod
    def compute_match(student_id: int, job_role_id: int | None = None) -> list[dict]:
        return compute_role_match(student_id, job_role_id)
