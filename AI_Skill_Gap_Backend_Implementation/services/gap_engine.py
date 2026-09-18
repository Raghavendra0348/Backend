"""
services/gap_engine.py — Skill gap analysis with ML + deterministic fallback.

Gap formula (deterministic baseline):
    gap       = max(0, required_level − current_level)
    gap_pct   = gap / required_level × 100
    priority  = gap_pct × importance

ML classification (when model is available):
    Predicts LOW / MEDIUM / HIGH from feature vector using trained sklearn pipeline.
    Falls back to deterministic classification if model not available or prediction fails.

Thresholds (starting points; calibrate with real labeled data):
    LOW    ≤ 20 %
    MEDIUM ≤ 50 %
    HIGH   > 50 %
"""
import logging
from pathlib import Path

from flask import current_app
from extensions import db
from models import StudentSkill, JobSkill, SkillGap

log = logging.getLogger(__name__)

# Deterministic thresholds — calibrated to be reasonable starting points
_THRESHOLDS = {"LOW": 20.0, "MEDIUM": 50.0}

# Lazy-loaded ML model
_model = None
_MODEL_VERSION = "gradient-boosted-v2"


def _load_model():
    """Load the trained sklearn model from MODEL_PATH config. Returns None if unavailable."""
    global _model
    if _model is not None:
        return _model
    try:
        path = Path(current_app.config.get("MODEL_PATH", "ml/models/skill_gap_model.joblib"))
        if path.exists():
            import joblib
            _model = joblib.load(str(path))
            log.info("[gap_engine] ML model loaded from %s", path)
        else:
            log.info("[gap_engine] Model not found at %s; using deterministic baseline.", path)
    except Exception as exc:
        log.warning("[gap_engine] Could not load ML model: %s", exc)
    return _model


def classify_gap(gap_percent: float) -> str:
    """
    Classify gap severity based on percentage gap.
    Proposed engineering thresholds — calibrate with labeled data.
    """
    if gap_percent <= _THRESHOLDS["LOW"]:
        return "LOW"
    if gap_percent <= _THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    return "HIGH"


def _predict_with_model(
    model,
    assessment_score: float,
    current: float,
    required: float,
    gap_percent: float,
    project_count: int,
    cert_count: int,
    importance: float,
    skill_category: str,
) -> str | None:
    """
    Use the trained ML model to predict gap severity.
    Returns None if prediction fails (triggers deterministic fallback).
    """
    try:
        import pandas as pd
        row = pd.DataFrame([{
            "gap_percent":          gap_percent,   # primary feature (v2 model)
            "assessment_score":     assessment_score,
            "current_proficiency":  current,
            "required_proficiency": required,
            "project_count":        project_count,
            "certification_count":  cert_count,
            "role_importance":      importance,
            "skill_category":       skill_category,
        }])
        return str(model.predict(row)[0])
    except Exception as exc:
        log.warning("[gap_engine] ML prediction failed: %s — falling back to deterministic.", exc)
        return None


def _derive_evidence_metadata(student_skill_rows, gap: float, current: float) -> tuple[str, float]:
    """
    Derive evidence summary string and evidence adjustment factor.
    Verified / assessment evidence maintains standard weight (1.0).
    Unverified or self-reported evidence increases priority urgency (factor > 1.0) when a gap exists.
    """
    if not student_skill_rows or current == 0.0:
        return "No evidence acquired", 1.0

    # Highest verification level among matching student skill rows
    evidence_types = {r.evidence_type.lower() for r in student_skill_rows if r.evidence_type}

    if "assessment" in evidence_types:
        return f"Verified by MCQ Assessment ({current:.0f}%)", 1.0
    if "certified" in evidence_types or "certification" in evidence_types:
        return f"Verified by Certification ({current:.0f}%)", 1.0
    if "resume" in evidence_types:
        factor = 1.05 if gap > 0 else 1.0
        return f"Extracted from Resume/Projects ({current:.0f}%)", factor
    if "reassessment" in evidence_types:
        return f"Verified by Reassessment ({current:.0f}%)", 1.0
    if "self_reported" in evidence_types:
        factor = 1.15 if gap > 0 else 1.0
        return f"Self-reported ({current:.0f}%) — unverified", factor

    return f"Recorded ({current:.0f}%)", 1.0


def generate_gap_explanation(
    skill_name: str,
    current: float,
    required: float,
    gap: float,
    gap_pct: float,
    severity: str,
    relation_type: str | None,
    evidence_summary: str,
) -> str:
    """Produce natural language explanation for the gap result."""
    rel_desc = "Essential requirement" if relation_type == "essential" else "Recommended competency"
    if gap == 0.0:
        return (
            f"Proficiency requirement fulfilled ({current:.1f}/{required:.1f}). "
            f"Evidence: {evidence_summary}."
        )

    return (
        f"{rel_desc} with {severity} gap: current proficiency is {current:.1f}/{required:.1f} "
        f"({gap:.1f} pt deficit, {gap_pct:.1f}% gap). Evidence: {evidence_summary}."
    )


def analyze(student_id: int, role_id: int) -> list[dict]:
    """
    Analyze skill gaps for a student against a target role.

    Source of truth:
      gap = max(0.0, required_level - current_level)
      gap_pct = (gap / required_level * 100) if required > 0 else 0.0
      priority_score = gap_pct * importance * evidence_factor
    """
    from models import Assessment, Project, Certification, Skill

    model = _load_model()
    model_version = "ml-logistic-v1" if model else "deterministic-baseline-v1"

    requirements = JobSkill.query.filter_by(job_role_id=role_id).all()
    if not requirements:
        return []

    # Pre-fetch student context for ML features
    project_count = Project.query.filter_by(student_id=student_id).count()
    cert_count = Certification.query.filter_by(student_id=student_id).count()

    results = []
    for req in requirements:
        from services.skill_normalizer import get_equivalent_skill_ids
        eq_ids = get_equivalent_skill_ids(req.skill_id)
        student_skill_rows = StudentSkill.query.filter(
            StudentSkill.student_id == student_id,
            StudentSkill.skill_id.in_(eq_ids)
        ).all()
        current = max([float(r.proficiency) for r in student_skill_rows] or [0.0])
        required = float(req.required_level)
        importance = float(req.importance if req.importance is not None else 1.0)

        # Deterministic formula as source of truth
        gap = max(0.0, required - current)
        gap_pct = (gap / required * 100) if required > 0 else 0.0

        # Evidence evaluation & priority adjustment
        evidence_summary, evidence_factor = _derive_evidence_metadata(
            student_skill_rows, gap, current
        )

        # Most recent assessment score across equivalent skills
        latest_assessment = Assessment.query.filter(
            Assessment.student_id == student_id,
            Assessment.skill_id.in_(eq_ids)
        ).order_by(Assessment.assessed_at.desc()).first()
        assessment_score = (
            latest_assessment.score / latest_assessment.max_score * 100
            if latest_assessment else current
        )

        # Skill category for ML categorical feature
        skill_obj = db.session.get(Skill, req.skill_id)
        skill_cat = skill_obj.category if skill_obj else "General"
        skill_name = skill_obj.name if skill_obj else str(req.skill_id)

        # Classify severity
        if model and gap > 0:
            severity = _predict_with_model(
                model, assessment_score, current, required,
                gap_pct, project_count, cert_count, importance, skill_cat
            ) or classify_gap(gap_pct)
        else:
            severity = classify_gap(gap_pct)

        priority = round(gap_pct * importance * evidence_factor, 2)

        explanation = generate_gap_explanation(
            skill_name=skill_name,
            current=current,
            required=required,
            gap=gap,
            gap_pct=gap_pct,
            severity=severity,
            relation_type=req.relation_type,
            evidence_summary=evidence_summary,
        )

        results.append({
            "skill_id": req.skill_id,
            "skill": skill_name,
            "current_level": current,
            "required_level": required,
            "gap": round(gap, 2),
            "gap_percent": round(gap_pct, 2),
            "severity": severity,
            "priority_score": priority,
            "relation_type": req.relation_type,
            "evidence_summary": evidence_summary,
            "evidence_factor": evidence_factor,
            "explanation": explanation,
            "model_version": model_version,
        })

    # Sort by priority descending (highest gap first)
    results.sort(key=lambda x: x["priority_score"], reverse=True)

    # Persist to DB (replace previous analysis for this student+role)
    SkillGap.query.filter_by(student_id=student_id, job_role_id=role_id).delete()
    for r in results:
        db.session.add(SkillGap(
            student_id=student_id,
            job_role_id=role_id,
            skill_id=r["skill_id"],
            current_level=r["current_level"],
            required_level=r["required_level"],
            gap_value=r["gap"],
            gap_percent=r["gap_percent"],
            severity=r["severity"],
            priority_score=r["priority_score"],
            evidence_summary=r["evidence_summary"],
            evidence_factor=r["evidence_factor"],
            explanation=r["explanation"],
            model_version=r["model_version"],
        ))
    db.session.commit()

    return results


class SkillGapService:
    @staticmethod
    def analyze(student_id: int, job_role_id: int) -> list[dict]:
        return analyze(student_id, job_role_id)

