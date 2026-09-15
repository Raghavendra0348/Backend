"""
services/analytics.py — Skill progress analytics for a student.

Computes:
  - Overall proficiency trend (start vs now)
  - Per-skill improvement history from Reassessment table
  - Top improved and regressed skills
  - Improvement velocity (avg gain per reassessment)
  - Time-series data points for frontend charts
  - Assessment performance trend
"""
from __future__ import annotations

from collections import defaultdict

from extensions import db
from models import Assessment, JobRole, Reassessment, Skill, SkillGap, StudentSkill


def compute_analytics(student_id: int) -> dict:
    """Return full skill progress analytics for a student."""

    # ── 1. Reassessment history ───────────────────────────────────────────────
    reassessments = (
        db.session.query(Reassessment, Skill)
        .join(Skill, Skill.id == Reassessment.skill_id)
        .filter(Reassessment.student_id == student_id)
        .order_by(Reassessment.assessed_at.asc())
        .all()
    )

    # Per-skill time series: {skill_name: [{date, level}]}
    skill_timeline: dict[str, list[dict]] = defaultdict(list)
    # Per-skill improvement: {skill_name: total_gain}
    skill_gain: dict[str, float] = defaultdict(float)
    # Per-skill first/last levels
    skill_first: dict[str, float] = {}
    skill_last:  dict[str, float] = {}

    total_improvements = 0
    total_gain_sum     = 0.0

    for ra, skill in reassessments:
        ts = ra.assessed_at.isoformat() if ra.assessed_at else None
        skill_timeline[skill.name].append({
            "date":  ts,
            "level": ra.new_level,
        })
        gain = float(ra.improvement or 0)
        skill_gain[skill.name] += gain
        total_gain_sum    += gain
        total_improvements += 1

        if skill.name not in skill_first:
            skill_first[skill.name] = float(ra.old_level or 0)
        skill_last[skill.name] = float(ra.new_level or 0)

    # ── 2. Top improved / regressed skills ────────────────────────────────────
    skill_gain_list = sorted(
        [{"skill": k, "gain": round(v, 2),
          "from": skill_first.get(k, 0), "to": skill_last.get(k, 0)}
         for k, v in skill_gain.items()],
        key=lambda x: x["gain"],
        reverse=True
    )
    top_improved  = [s for s in skill_gain_list if s["gain"] > 0][:5]
    top_regressed = [s for s in reversed(skill_gain_list) if s["gain"] < 0][:3]

    # ── 3. Current skill snapshot ─────────────────────────────────────────────
    current_skills = StudentSkill.query.filter_by(student_id=student_id).all()
    avg_now    = (
        round(sum(ss.proficiency for ss in current_skills) / len(current_skills), 2)
        if current_skills else 0.0
    )
    skills_above_70 = sum(1 for ss in current_skills if ss.proficiency >= 70)
    skills_above_50 = sum(1 for ss in current_skills if ss.proficiency >= 50)

    # ── 4. Assessment performance ─────────────────────────────────────────────
    assessments = (
        db.session.query(Assessment, Skill)
        .join(Skill, Skill.id == Assessment.skill_id)
        .filter(Assessment.student_id == student_id)
        .order_by(Assessment.assessed_at.asc())
        .all()
    )
    assessment_scores = [
        {
            "skill":  skill.name,
            "score":  round(a.score / a.max_score * 100, 2) if a.max_score else 0,
            "date":   a.assessed_at.isoformat() if a.assessed_at else None,
            "attempt": a.attempt_no,
        }
        for a, skill in assessments
    ]
    avg_assessment = (
        round(sum(a["score"] for a in assessment_scores) / len(assessment_scores), 2)
        if assessment_scores else None
    )

    # ── 5. Gap summary across all roles ───────────────────────────────────────
    gap_summary = (
        db.session.query(
            SkillGap.severity,
            db.func.count(SkillGap.id).label("count")
        )
        .filter(SkillGap.student_id == student_id)
        .group_by(SkillGap.severity)
        .all()
    )
    gap_counts = {row.severity: row.count for row in gap_summary}

    # ── 6. Best-fit role (if gaps exist) ─────────────────────────────────────
    best_role = None
    role_gap_counts = (
        db.session.query(
            SkillGap.job_role_id,
            db.func.count(SkillGap.id).label("total"),
            db.func.sum(
                db.case((SkillGap.severity == "HIGH", 1), else_=0)
            ).label("high_count"),
        )
        .filter(SkillGap.student_id == student_id)
        .group_by(SkillGap.job_role_id)
        .order_by(db.literal_column("high_count").asc())
        .first()
    )
    if role_gap_counts:
        role = db.session.get(JobRole, role_gap_counts.job_role_id)
        if role:
            best_role = {
                "role":        role.name,
                "high_gaps":   int(role_gap_counts.high_count or 0),
                "total_gaps":  int(role_gap_counts.total),
            }

    # ── 7. Improvement velocity ───────────────────────────────────────────────
    velocity = (
        round(total_gain_sum / total_improvements, 2)
        if total_improvements > 0 else 0.0
    )

    return {
        "summary": {
            "total_skills":          len(current_skills),
            "skills_above_70":       skills_above_70,
            "skills_above_50":       skills_above_50,
            "avg_proficiency":       avg_now,
            "total_reassessments":   total_improvements,
            "total_gain":            round(total_gain_sum, 2),
            "avg_gain_per_session":  velocity,
            "avg_assessment_score":  avg_assessment,
        },
        "top_improved_skills":   top_improved,
        "regressed_skills":      top_regressed,
        "skill_trends":          {k: v for k, v in skill_timeline.items()},
        "assessment_history":    assessment_scores,
        "gap_severity_counts":   gap_counts,
        "best_fit_role":         best_role,
    }
