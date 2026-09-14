"""
services/recommender.py — Content-based recommendation engine.

Ranking formula (per PRD Section 12.5):
    score = 0.5 × content_similarity
          + 0.3 × min(priority_score / 100, 1.0)
          + 0.2 × (course_rating / 5.0)

Content similarity uses TF-IDF cosine over course description+title+skill tags
compared against a pseudo-document built from the gap skill's name + category.

Recommendations are persisted to the recommendations table.
"""
import logging
import math
from collections import defaultdict

from extensions import db
from models import SkillGap, Skill, Course, CourseSkill, Recommendation

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Lightweight TF-IDF implementation (no external ML dependency at runtime)
# ─────────────────────────────────────────────────────────────────────────────
import re


def _tokenize(text: str) -> list[str]:
    """Lowercase, split on whitespace/punctuation, return token list."""
    return re.findall(r"[a-z0-9\+\#]+", (text or "").lower())


def _tfidf_vectors(documents: list[list[str]]) -> tuple[list[dict], dict]:
    """
    Compute TF-IDF vectors for a list of tokenized documents.
    Returns (vectors, idf_map) where each vector is a dict {term: tfidf}.
    """
    N = len(documents)
    if N == 0:
        return [], {}

    # IDF
    df: dict[str, int] = defaultdict(int)
    for doc in documents:
        for term in set(doc):
            df[term] += 1
    idf = {term: math.log(N / (1 + count)) for term, count in df.items()}

    # TF × IDF
    vectors = []
    for doc in documents:
        tf: dict[str, float] = defaultdict(float)
        for term in doc:
            tf[term] += 1
        total = len(doc) or 1
        vec = {term: (count / total) * idf.get(term, 0)
               for term, count in tf.items()}
        vectors.append(vec)
    return vectors, idf


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
    return dot / (mag_a * mag_b)


# ─────────────────────────────────────────────────────────────────────────────
# Main Recommender
# ─────────────────────────────────────────────────────────────────────────────
def recommend(student_id: int, top_k: int = 10) -> list[dict]:
    """
    Generate top-K personalized course recommendations for a student.

    Uses the persisted SkillGap records and CourseSkill relevance mappings.
    Falls back to explicit CourseSkill matching when TF-IDF similarity is 0.
    """
    # Fetch skill gaps ordered by priority
    gaps = (
        db.session.query(SkillGap, Skill)
        .join(Skill, Skill.id == SkillGap.skill_id)
        .filter(SkillGap.student_id == student_id, SkillGap.gap_value > 0)
        .order_by(SkillGap.priority_score.desc())
        .all()
    )
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

    course_vecs, _ = _tfidf_vectors(course_docs)

    # Build skill-indexed CourseSkill relevance map
    skill_course_relevance: dict[int, dict[int, float]] = defaultdict(dict)
    for cs in CourseSkill.query.all():
        skill_course_relevance[cs.skill_id][cs.course_id] = float(cs.relevance or 0)

    scored: dict[int, dict] = {}  # course_id → best scored item

    for gap, skill in gaps:
        # Query vector for this gap skill
        query_text = f"{skill.name} {skill.category or ''} {skill.description or ''}"
        query_vec, _ = _tfidf_vectors([_tokenize(query_text)])
        q_vec = query_vec[0] if query_vec else {}

        for idx, course in enumerate(all_courses):
            # Content similarity
            content_sim = _cosine(q_vec, course_vecs[idx]) if q_vec else 0.0

            # Explicit skill mapping bonus
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

            if course.id not in scored or scored[course.id]["score"] < score:
                scored[course.id] = {
                    "skill_id":   skill.id,
                    "skill":      skill.name,
                    "course_id":  course.id,
                    "title":      course.title,
                    "provider":   course.provider,
                    "url":        course.url,
                    "difficulty": course.difficulty_level,
                    "rating":     course.rating,
                    "score":      round(score, 4),
                    "reason": (
                        f"Addresses your {skill.name} gap of "
                        f"{gap.gap_percent:.1f}% (priority {gap.priority_score:.1f}). "
                        f"Content match: {content_sim:.2f}."
                    ),
                }

    out = sorted(scored.values(), key=lambda x: x["score"], reverse=True)[:top_k]

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
