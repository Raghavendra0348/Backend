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
from models import SkillGap, Skill, Course, CourseSkill, Recommendation

log = logging.getLogger(__name__)

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
) -> list[dict]:
    """
    Generate top-K personalized course recommendations for a student.

    Uses the persisted SkillGap records and CourseSkill relevance mappings.
    Falls back to explicit CourseSkill matching when TF-IDF similarity is 0.
    Ensures skill diversity across top recommendations so distinct gap areas
    are prioritized before recommending multiple courses for the same skill.
    """
    # Fetch skill gaps ordered by priority
    query = (
        db.session.query(SkillGap, Skill)
        .join(Skill, Skill.id == SkillGap.skill_id)
        .filter(SkillGap.student_id == student_id, SkillGap.gap_value > 0)
    )

    if job_role_id:
        query = query.filter(SkillGap.job_role_id == job_role_id)
    else:
        # If no role specified, filter to the most recently evaluated role
        latest_gap = (
            SkillGap.query
            .filter(SkillGap.student_id == student_id, SkillGap.gap_value > 0)
            .order_by(SkillGap.id.desc())
            .first()
        )
        if latest_gap and latest_gap.job_role_id:
            query = query.filter(SkillGap.job_role_id == latest_gap.job_role_id)

    gaps = query.order_by(SkillGap.priority_score.desc()).all()
    if not gaps:
        return []

    # Fetch all courses with their skill mappings
    all_courses = Course.query.all()
    if not all_courses:
        return []

    # Build course text documents for TF-IDF
    course_docs = []
    for course in all_courses:
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

    # Also build alias mappings: for each gap skill, find all equivalent skill IDs
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
        # Query vector for this gap skill
        query_text = f"{skill.name} {skill.category or ''} {skill.description or ''}"
        q_vec = _vectorize(_tokenize(query_text), idf_map)

        for idx, course in enumerate(all_courses):
            # Content similarity (guaranteed non-negative)
            content_sim = _cosine(q_vec, course_vecs[idx]) if q_vec else 0.0

            # Explicit skill mapping bonus (alias-aware)
            mapping_relevance = alias_relevance[skill.id].get(course.id, 0.0)
            if mapping_relevance == 0.0:
                mapping_relevance = skill_course_relevance[skill.id].get(course.id, 0.0)

            # If there's no content similarity and no mapping, skip
            if content_sim == 0.0 and mapping_relevance == 0.0:
                continue

            # If skill mapping exists, use it as a floor for content similarity
            effective_sim = max(content_sim, mapping_relevance * 0.8)

            # Rating normalised to 0–1 (Coursera: 0–5)
            rating_norm = min(float(course.rating or 0), 5.0) / 5.0

            priority_norm = min(float(gap.priority_score) / 100.0, 1.0)

            score = (
                0.5 * effective_sim
                + 0.3 * priority_norm
                + 0.2 * rating_norm
            )

            if score <= 0:
                continue

            match_pct = int(round(min(max(effective_sim, 0.0), 1.0) * 100))
            reason = (
                f"Addresses your {skill.name} gap of "
                f"{gap.gap_percent:.1f}% (priority {gap.priority_score:.1f}). "
                f"Content match: {match_pct}%."
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
            })

    # Sort all candidates by score descending
    candidates.sort(key=lambda x: x["score"], reverse=True)

    # Diversity-aware ranking:
    # Ensure distinct skills get recommended first so multiple courses for the same skill
    # don't crowd out other high-priority gaps.
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

    # Persist recommendations (replace previous ones for this student)
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
