"""
services/skill_service.py — Skill catalogue and resolution business logic.
"""
from extensions import db
from models import Skill
from services.skill_normalizer import canonicalize_skill_name


class SkillService:
    @staticmethod
    def list_skills(search: str = "", category: str = "", limit: int = 100) -> dict:
        """Fetch skills catalogue matching search criteria and return distinct categories."""
        limit = min(max(int(limit), 1), 500)
        q = Skill.query
        if search:
            q = q.filter(Skill.name.ilike(f"%{search.strip()}%"))
        if category:
            q = q.filter(Skill.category == category.strip())
        skills = q.order_by(Skill.name).limit(limit).all()

        categories = [
            r[0] for r in
            db.session.query(Skill.category).distinct().order_by(Skill.category).all()
            if r[0]
        ]

        return {
            "total": len(skills),
            "categories": categories,
            "skills": [s.to_dict() for s in skills],
        }

    @staticmethod
    def get_skill(skill_id: int):
        """Retrieve a single skill by primary key."""
        return db.session.get(Skill, skill_id)

    @staticmethod
    def resolve_skill_id(skill_id: int | None = None,
                         skill_name_raw: str | None = None,
                         category: str = "General",
                         source: str = "MANUAL") -> int | None:
        """
        Resolve skill_id either from ID or canonicalized skill_name.
        If non-existent and skill_name provided, registers canonical skill.
        """
        if skill_id:
            return skill_id if db.session.get(Skill, skill_id) else None
        if not skill_name_raw:
            return None

        sk_name = canonicalize_skill_name(str(skill_name_raw).strip())
        if not sk_name:
            return None

        sk = Skill.query.filter(db.func.lower(Skill.name) == sk_name.lower()).first()
        if not sk:
            sk = Skill(name=sk_name, category=category, source=source)
            db.session.add(sk)
            db.session.flush()
        return sk.id
