"""
services/role_service.py — Job role and role-skill requirement business logic.
"""
from extensions import db
from models import JobRole, JobSkill, Skill


class RoleService:
    @staticmethod
    def list_roles() -> list[dict]:
        """Fetch all available job roles ordered by name."""
        roles = JobRole.query.order_by(JobRole.name).all()
        return [r.to_dict() for r in roles]

    @staticmethod
    def get_role_skills(role_id: int, category_filter: str = "all") -> tuple[dict | None, str | None, int]:
        """
        Return the required skills for a role with dual-taxonomy breakdown (ESCO + O*NET).
        """
        role = db.session.get(JobRole, role_id)
        if not role:
            return None, "role not found", 404

        cat_filter = (category_filter or "all").lower()

        rows = (
            db.session.query(JobSkill, Skill)
            .join(Skill, Skill.id == JobSkill.skill_id)
            .filter(JobSkill.job_role_id == role_id)
            .all()
        )

        filtered_rows = []
        for js, sk in rows:
            cat = (sk.category or "").lower()
            if cat_filter == "technical" and "o*net" in cat:
                continue
            elif cat_filter == "knowledge" and cat != "o*net knowledge":
                continue
            elif cat_filter == "activity" and cat != "o*net work activity":
                continue
            filtered_rows.append((js, sk))

        total_technical = sum(1 for _, sk in rows if "o*net" not in (sk.category or "").lower())
        total_knowledge = sum(1 for _, sk in rows if (sk.category or "").lower() == "o*net knowledge")
        total_activity = sum(1 for _, sk in rows if (sk.category or "").lower() == "o*net work activity")

        result = {
            "role": role.to_dict(),
            "role_id": role.id,
            "role_name": role.name,
            "onet_code": role.onet_code,
            "esco_uri": role.source_identifier,
            "technical_skills_count": total_technical,
            "onet_competencies_count": total_knowledge + total_activity,
            "total_skills": len(rows),
            "filtered_count": len(filtered_rows),
            "category_filter": cat_filter,
            "required_skills": [
                {
                    "skill_id": sk.id,
                    "skill": sk.name,
                    "category": sk.category,
                    "source": js.source or sk.source,
                    "required_level": js.required_level,
                    "importance": js.importance,
                    "relation_type": js.relation_type,
                }
                for js, sk in filtered_rows
            ],
        }
        return result, None, 200
