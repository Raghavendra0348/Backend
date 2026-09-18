"""
services/student_service.py — Student management business logic.
"""
from extensions import db
from models import Student, StudentSkill, Skill
import cache as _cache
from services.skill_service import SkillService


class StudentService:
    @staticmethod
    def create_student(data: dict) -> tuple[Student | None, str | None, int]:
        """Create a new student profile. Validates name and duplicate email."""
        name = (data.get("name") or "").strip()
        email = (data.get("email") or "").strip()

        if not name or not email:
            return None, "name and email are required", 400

        if Student.query.filter_by(email=email).first():
            return None, "email already registered", 409

        student = Student(
            name=name,
            email=email,
            course=data.get("course"),
            year=data.get("year"),
            target_career=data.get("target_career"),
        )
        db.session.add(student)
        db.session.commit()
        return student, None, 201

    @staticmethod
    def list_students(limit: int = 50) -> list[dict]:
        """List recent students."""
        limit = min(max(int(limit), 1), 100)
        students = Student.query.order_by(Student.id.desc()).limit(limit).all()
        return [s.to_dict() for s in students]

    @staticmethod
    def get_student(student_id: int) -> Student | None:
        """Find student by primary key."""
        return db.session.get(Student, student_id)

    @staticmethod
    def get_student_profile(student_id: int) -> dict | None:
        """Get student profile dictionary populated with active skills."""
        student = db.session.get(Student, student_id)
        if not student:
            return None

        rows = (
            db.session.query(StudentSkill, Skill)
            .join(Skill, Skill.id == StudentSkill.skill_id)
            .filter(StudentSkill.student_id == student_id)
            .all()
        )

        return {
            **student.to_dict(),
            "skills": [
                {
                    "skill_id": sk.id,
                    "skill": sk.name,
                    "category": sk.category,
                    "proficiency": ss.proficiency,
                    "evidence_type": ss.evidence_type,
                    "confidence": ss.confidence,
                }
                for ss, sk in rows
            ],
        }

    @staticmethod
    def update_student(student_id: int, data: dict) -> Student | None:
        """Update mutable student fields."""
        student = db.session.get(Student, student_id)
        if not student:
            return None

        for field in ("name", "course", "year", "target_career"):
            if field in data:
                setattr(student, field, data[field])
        db.session.commit()
        return student

    @staticmethod
    def add_or_update_skill(student_id: int,
                            skill_id: int | None = None,
                            skill_name: str | None = None,
                            proficiency: float = 0.0,
                            evidence_type: str = "self_reported") -> tuple[dict | None, str | None, int]:
        """Add or update proficiency level for a skill."""
        student = db.session.get(Student, student_id)
        if not student:
            return None, "student not found", 404

        resolved_id = SkillService.resolve_skill_id(skill_id, skill_name)
        if not resolved_id:
            return None, "skill_id or valid skill_name is required", 400

        try:
            prof = float(proficiency)
        except (TypeError, ValueError):
            return None, "proficiency must be a number", 400

        if not 0 <= prof <= 100:
            return None, "proficiency must be between 0 and 100", 400

        ss = StudentSkill.query.filter_by(
            student_id=student_id, skill_id=resolved_id
        ).first()

        if ss:
            ss.proficiency = prof
            ss.evidence_type = evidence_type
        else:
            ss = StudentSkill(
                student_id=student_id,
                skill_id=resolved_id,
                proficiency=prof,
                evidence_type=evidence_type,
            )
            db.session.add(ss)

        _cache.invalidate_student(student_id)
        db.session.commit()

        return {
            "student_id": student_id,
            "skill_id": resolved_id,
            "proficiency": prof,
            "evidence_type": evidence_type,
        }, None, 200
