"""
services/assessment_service.py — Assessment and reassessment business logic.
"""
from extensions import db
from models import Assessment, Reassessment, Student, StudentSkill, JobRole
from services.skill_service import SkillService
from services.gap_engine import analyze
import cache as _cache


class AssessmentService:
    @staticmethod
    def submit_assessment(student_id: int, data: dict) -> tuple[dict | None, str | None, int]:
        """Submit assessment result; derives and persists proficiency."""
        student = db.session.get(Student, student_id)
        if not student:
            return None, "student not found", 404

        skill_id = SkillService.resolve_skill_id(data.get("skill_id"), data.get("skill_name"))
        if not skill_id:
            return None, "skill_id or valid skill_name is required", 400

        try:
            score = float(data.get("score", 0))
            maximum = float(data.get("max_score", 100))
        except (TypeError, ValueError):
            return None, "score and max_score must be numbers", 400

        if maximum <= 0 or not 0 <= score <= maximum:
            return None, f"score must be 0–{maximum}", 400

        prev = Assessment.query.filter_by(
            student_id=student_id, skill_id=skill_id
        ).count()

        a = Assessment(
            student_id=student_id,
            skill_id=skill_id,
            score=score,
            max_score=maximum,
            attempt_no=prev + 1,
        )
        db.session.add(a)

        prof = round(score / maximum * 100, 2)
        row = StudentSkill.query.filter_by(
            student_id=student_id, skill_id=skill_id
        ).first()

        if row:
            row.proficiency = prof
            row.evidence_type = "assessment"
        else:
            db.session.add(StudentSkill(
                student_id=student_id,
                skill_id=skill_id,
                proficiency=prof,
                evidence_type="assessment",
            ))

        _cache.invalidate_student(student_id)
        db.session.commit()

        return {
            "assessment_id": a.id,
            "proficiency": prof,
            "attempt_no": a.attempt_no,
        }, None, 201

    @staticmethod
    def submit_reassessment(student_id: int, data: dict) -> tuple[dict | None, str | None, int]:
        """Submit reassessment, update student skills, and recalculate gaps if role provided."""
        student = db.session.get(Student, student_id)
        if not student:
            return None, "student not found", 404

        skill_id = SkillService.resolve_skill_id(data.get("skill_id"), data.get("skill_name"))
        if not skill_id:
            return None, "skill_id or valid skill_name is required", 400

        try:
            if "new_level" in data:
                new_level = float(data["new_level"])
            elif "score" in data and "max_score" in data:
                new_level = round(float(data["score"]) / float(data["max_score"]) * 100, 2)
            else:
                new_level = float(data.get("new_level", 0))
        except (TypeError, ValueError, ZeroDivisionError):
            return None, "new_level or score/max_score must be numbers", 400

        if not 0 <= new_level <= 100:
            return None, "new_level must be between 0 and 100", 400

        row = StudentSkill.query.filter_by(
            student_id=student_id, skill_id=skill_id
        ).first()
        old_level = float(row.proficiency) if row else 0.0

        if row:
            row.proficiency = new_level
            row.evidence_type = "reassessment"
        else:
            db.session.add(StudentSkill(
                student_id=student_id,
                skill_id=skill_id,
                proficiency=new_level,
                evidence_type="reassessment",
            ))

        r = Reassessment(
            student_id=student_id,
            skill_id=skill_id,
            old_level=old_level,
            new_level=new_level,
            improvement=round(new_level - old_level, 2),
        )
        db.session.add(r)
        _cache.invalidate_student(student_id)
        db.session.commit()

        result = {
            "old_level": old_level,
            "new_level": new_level,
            "improvement": r.improvement,
        }

        job_role_id = data.get("job_role_id")
        if job_role_id and db.session.get(JobRole, job_role_id):
            updated_gaps = analyze(student_id, int(job_role_id))
            result["updated_gaps"] = updated_gaps

        return result, None, 201
