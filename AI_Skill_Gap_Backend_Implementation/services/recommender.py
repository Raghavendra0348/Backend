"""
services/recommender.py — Content-based recommendation engine.

Ranking formula (per PRD Section 12.5):
    score = 0.5 × content_similarity
          + 0.3 × min(priority_score / 100, 1.0)
          + 0.2 × (course_rating / 5.0)

Content similarity uses TF-IDF cosine over course description+title+skill tags
compared against a query vector built from the gap skill's name + category.

Recommendations are persisted to the recommendations table.
"""
import logging
import math
import re
from collections import defaultdict

from extensions import db
from models import (
    SkillGap, Skill, Course, CourseSkill, Recommendation,
    RecommendationRun, LearningProgress
)

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Configurable Scoring Weights (PRD / Staged Plan Stage 7)
# ─────────────────────────────────────────────────────────────────────────────
DEFAULT_WEIGHTS: dict[str, float] = {
    "skill_gap_relevance": 0.35,
    "learning_level_fit": 0.20,
    "content_similarity": 0.15,
    "quality": 0.10,
    "user_preference": 0.10,
    "diversity": 0.10,
}


def normalize_weights(custom_weights: dict[str, float] | None = None) -> dict[str, float]:
    """Merge custom weights into defaults and normalize so they sum to 1.0."""
    w = dict(DEFAULT_WEIGHTS)
    if custom_weights:
        for k, v in custom_weights.items():
            if k in w and isinstance(v, (int, float)) and v >= 0:
                w[k] = float(v)
    total = sum(w.values())
    if total <= 0:
        return dict(DEFAULT_WEIGHTS)
    return {k: round(v / total, 4) for k, v in w.items()}


def _compute_level_fit(current_level: float, difficulty: str | None) -> float:
    """
    Score how well course difficulty fits student's current proficiency (0.0 to 1.0):
      - Beginner: optimal for proficiency < 35%
      - Intermediate: optimal for 30%–75%
      - Advanced: optimal for > 65%
    """
    diff = (difficulty or "").strip().lower()
    if diff == "beginner":
        if current_level < 35.0:
            return 1.0
        elif current_level < 65.0:
            return 0.70
        else:
            return 0.35
    elif diff == "intermediate":
        if 30.0 <= current_level <= 75.0:
            return 1.0
        elif current_level < 30.0:
            return 0.65
        else:
            return 0.60
    elif diff == "advanced":
        if current_level >= 65.0:
            return 1.0
        elif current_level >= 40.0:
            return 0.60
        else:
            return 0.25
    return 0.70


# ─────────────────────────────────────────────────────────────────────────────
# Lightweight TF-IDF implementation (no external ML dependency at runtime)
# ─────────────────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> list[str]:
    """Lowercase, split on whitespace/punctuation, return token list."""
    return re.findall(r"[a-z0-9\+\#]+", (text or "").lower())


def _build_idf_map(documents: list[list[str]]) -> dict[str, float]:
    """
    Compute smooth IDF map for a corpus of tokenized documents:
        idf(t) = ln((1 + N) / (1 + df(t))) + 1.0
    Guaranteed strictly positive (>= 1.0) for all corpus terms.
    """
    N = len(documents)
    if N == 0:
        return {}

    df: dict[str, int] = defaultdict(int)
    for doc in documents:
        for term in set(doc):
            df[term] += 1

    return {
        term: math.log((1 + N) / (1 + count)) + 1.0
        for term, count in df.items()
    }


def _vectorize(tokens: list[str], idf_map: dict[str, float]) -> dict[str, float]:
    """
    Compute TF-IDF vector for a list of tokens using a precomputed IDF map.
    Returns {term: tfidf_weight}. All weights are non-negative.
    """
    if not tokens:
        return {}
    tf: dict[str, float] = defaultdict(float)
    for term in tokens:
        tf[term] += 1.0
    total = len(tokens)
    return {
        term: (count / total) * idf_map.get(term, 1.0)
        for term, count in tf.items()
    }


def _cosine(a: dict, b: dict) -> float:
    """Cosine similarity between two TF-IDF vectors represented as dicts."""
    shared = set(a) & set(b)
    if not shared:
        return 0.0
    dot = sum(a[t] * b[t] for t in shared)
    mag_a = math.sqrt(sum(v * v for v in a.values()))
    mag_b = math.sqrt(sum(v * v for v in b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return max(0.0, min(1.0, dot / (mag_a * mag_b)))


# ─────────────────────────────────────────────────────────────────────────────
# Main Recommender
# ─────────────────────────────────────────────────────────────────────────────
def recommend(
    student_id: int,
    top_k: int = 10,
    job_role_id: int | None = None,
    role_id: int | None = None,
    weights: dict[str, float] | None = None,
) -> list[dict]:
    """
    Generate top-K personalized course recommendations for a student.

    Uses a multi-factor intelligence pipeline:
      - 0.35 skill_gap_relevance
      - 0.20 learning_level_fit
      - 0.15 content_similarity
      - 0.10 quality rating
      - 0.10 user_preference signals (completed courses excluded, enrolled boosted)
      - 0.10 diversity
    Persists active recommendations and snapshots the run to recommendation_runs.
    """
    effective_role_id = job_role_id if job_role_id is not None else role_id
    w = normalize_weights(weights)

    # Fetch skill gaps ordered by priority
    query = (
        db.session.query(SkillGap, Skill)
        .join(Skill, Skill.id == SkillGap.skill_id)
        .filter(SkillGap.student_id == student_id, SkillGap.gap_value > 0)
    )

    if effective_role_id:
        query = query.filter(SkillGap.job_role_id == effective_role_id)
    else:
        latest_gap = (
            SkillGap.query
            .filter(SkillGap.student_id == student_id, SkillGap.gap_value > 0)
            .order_by(SkillGap.id.desc())
            .first()
        )
        if latest_gap and latest_gap.job_role_id:
            effective_role_id = latest_gap.job_role_id
            query = query.filter(SkillGap.job_role_id == latest_gap.job_role_id)

    gaps = query.order_by(SkillGap.priority_score.desc()).all()
    if not gaps:
        return []

    # Fetch all courses with their skill mappings
    all_courses = Course.query.all()
    if not all_courses:
        return []

    # Check student learning progress for preference signals
    learning_progress_rows = LearningProgress.query.filter_by(student_id=student_id).all()
    completed_course_ids = {
        lp.course_id for lp in learning_progress_rows
        if lp.course_id and (lp.status == "completed" or (lp.completion or 0) >= 100.0)
    }
    in_progress_course_ids = {
        lp.course_id for lp in learning_progress_rows
        if lp.course_id and lp.status == "in_progress"
    }
    preferred_providers = {
        c.provider for c in all_courses
        if c.id in completed_course_ids and c.provider
    }

    # Build course text documents for TF-IDF
    course_docs = []
    provider_frequencies = defaultdict(int)
    for course in all_courses:
        provider_frequencies[course.provider or "unknown"] += 1
        skill_names = [
            cs_row.skill_name
            for cs_row in db.session.query(Skill.name.label("skill_name"))
            .join(CourseSkill, CourseSkill.skill_id == Skill.id)
            .filter(CourseSkill.course_id == course.id)
            .all()
        ]
        doc_text = " ".join(filter(None, [
            course.title or "",
            course.description or "",
            course.provider or "",
            " ".join(skill_names),
        ]))
        course_docs.append(_tokenize(doc_text))

    idf_map = _build_idf_map(course_docs)
    course_vecs = [_vectorize(doc, idf_map) for doc in course_docs]

    # Build skill-indexed CourseSkill relevance map (alias-aware)
    from services.skill_normalizer import get_equivalent_skill_ids
    skill_course_relevance: dict[int, dict[int, float]] = defaultdict(dict)
    for cs in CourseSkill.query.all():
        skill_course_relevance[cs.skill_id][cs.course_id] = float(cs.relevance or 0)

    alias_relevance: dict[int, dict[int, float]] = defaultdict(dict)
    for gap, skill in gaps:
        eq_ids = get_equivalent_skill_ids(skill.id)
        for eq_id in eq_ids:
            if eq_id in skill_course_relevance:
                for cid, rel in skill_course_relevance[eq_id].items():
                    existing = alias_relevance[skill.id].get(cid, 0)
                    alias_relevance[skill.id][cid] = max(existing, rel)

    candidates: list[dict] = []

    for gap, skill in gaps:
        curr_level = float(gap.current_level or 0.0)
        query_text = f"{skill.name} {skill.category or ''} {skill.description or ''}"
        q_vec = _vectorize(_tokenize(query_text), idf_map)

        # Gap priority relevance (0 to 1)
        priority_norm = min(float(gap.priority_score or 0) / 100.0, 1.0)
        gap_mag = min(float(gap.gap_percent or 0) / 100.0, 1.0)
        skill_gap_relevance = min(1.0, round(0.7 * priority_norm + 0.3 * gap_mag, 4))

        for idx, course in enumerate(all_courses):
            # Exclude courses the student has already completed
            if course.id in completed_course_ids:
                continue

            # Content similarity
            content_sim = _cosine(q_vec, course_vecs[idx]) if q_vec else 0.0
            mapping_relevance = alias_relevance[skill.id].get(course.id, 0.0)
            if mapping_relevance == 0.0:
                mapping_relevance = skill_course_relevance[skill.id].get(course.id, 0.0)

            if content_sim == 0.0 and mapping_relevance == 0.0:
                continue

            effective_sim = max(content_sim, mapping_relevance * 0.8)

            # Learning level / difficulty fit (0 to 1)
            level_fit = _compute_level_fit(curr_level, course.difficulty_level)

            # Quality rating (0 to 1)
            rating_norm = (min(float(course.rating or 0), 5.0) / 5.0) if (course.rating and course.rating > 0) else 0.70

            # User preference signals (0 to 1)
            if course.id in in_progress_course_ids:
                user_pref = 1.0
            elif course.provider in preferred_providers:
                user_pref = 0.85
            else:
                user_pref = 0.50

            # Diversity score
            prov_count = provider_frequencies.get(course.provider or "unknown", 1)
            diversity_score = max(0.3, min(1.0, round(1.0 / math.sqrt(prov_count) * 1.5, 3)))

            # 6-Factor weighted score
            score = (
                w["skill_gap_relevance"] * skill_gap_relevance
                + w["learning_level_fit"] * level_fit
                + w["content_similarity"] * effective_sim
                + w["quality"] * rating_norm
                + w["user_preference"] * user_pref
                + w["diversity"] * diversity_score
            )

            if score <= 0:
                continue

            match_pct = int(round(min(max(effective_sim, 0.0), 1.0) * 100))
            diff_label = course.difficulty_level or "Suitable"
            reason = (
                f"Addresses your {skill.name} gap of {gap.gap_percent:.1f}% "
                f"(priority {gap.priority_score:.1f}). {diff_label} difficulty fits your "
                f"{curr_level:.1f}% proficiency. Content match: {match_pct}%. Rating: {course.rating or 4.0}★."
            )

            candidates.append({
                "skill_id":       skill.id,
                "skill":          skill.name,
                "course_id":      course.id,
                "title":          course.title,
                "provider":       course.provider,
                "url":            course.url,
                "difficulty":     course.difficulty_level,
                "rating":         course.rating,
                "score":          round(score, 4),
                "reason":         reason,
                "priority_score": gap.priority_score,
                "level_fit":      round(level_fit, 2),
                "content_match":  match_pct,
            })

    # Sort candidates by score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # Diversity-aware ranking
    seen_skills = set()
    seen_courses = set()
    first_pass = []
    remaining = []

    for c in candidates:
        if c["course_id"] in seen_courses:
            continue
        if c["skill_id"] not in seen_skills:
            first_pass.append(c)
            seen_skills.add(c["skill_id"])
            seen_courses.add(c["course_id"])
        else:
            remaining.append(c)

    out = first_pass[:top_k]
    if len(out) < top_k:
        for c in remaining:
            if c["course_id"] not in seen_courses:
                out.append(c)
                seen_courses.add(c["course_id"])
                if len(out) == top_k:
                    break

    # Persist snapshot to recommendation_runs
    try:
        run_record = RecommendationRun(
            student_id=student_id,
            job_role_id=effective_role_id,
            weights_used=w,
            total_recommendations=len(out),
            recommendations_snapshot=out,
        )
        db.session.add(run_record)
    except Exception as exc:
        log.warning("Failed to record recommendation run: %s", exc)

    # Persist active recommendations (replace previous ones for this student)
    Recommendation.query.filter_by(student_id=student_id).delete()
    for item in out:
        db.session.add(Recommendation(
            student_id=student_id,
            skill_id=item["skill_id"],
            course_id=item["course_id"],
            title=item["title"],
            url=item.get("url"),
            score=item["score"],
            reason=item["reason"],
        ))
    db.session.commit()

    return out


def get_recommendation_runs(student_id: int, limit: int = 10) -> list[dict]:
    """Retrieve historical recommendation run snapshots for a student."""
    runs = (
        RecommendationRun.query.filter_by(student_id=student_id)
        .order_by(RecommendationRun.created_at.desc())
        .limit(limit)
        .all()
    )
    return [r.to_dict() for r in runs]

