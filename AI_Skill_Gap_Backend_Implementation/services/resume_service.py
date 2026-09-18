"""
services/resume_service.py — Resume parsing, project, and certification business logic.
"""
import json
import logging
from pathlib import Path
import time
from werkzeug.utils import secure_filename
from extensions import db
import cache as _cache
from models import (
    Project, Certification, Resume, Student, Skill, StudentSkill,
    SkillEvidence, AIExtractionRecord, UnknownSkillReview, _utcnow
)
from services.resume_parser import (
    extract_text, candidate_skills, extract_skills_with_evidence,
    extract_projects_text, extract_certifications_text,
)

log = logging.getLogger(__name__)
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


class ResumeService:
    @staticmethod
    def add_project(student_id: int, data: dict) -> tuple[dict | None, str | None, int]:
        """Add a student project."""
        student = db.session.get(Student, student_id)
        if not student:
            return None, "student not found", 404

        title = (data.get("title") or "").strip()
        if not title:
            return None, "title is required", 400

        skills_used = data.get("skills_used")
        if isinstance(skills_used, list):
            skills_used = ", ".join(str(s) for s in skills_used)

        p = Project(
            student_id=student_id,
            title=title,
            description=data.get("description"),
            skills_used=skills_used,
        )
        db.session.add(p)
        db.session.commit()
        return {"id": p.id, "title": p.title}, None, 201

    @staticmethod
    def add_certification(student_id: int, data: dict) -> tuple[dict | None, str | None, int]:
        """Add a student certification."""
        student = db.session.get(Student, student_id)
        if not student:
            return None, "student not found", 404

        name = (data.get("name") or "").strip()
        if not name:
            return None, "name is required", 400

        c = Certification(
            student_id=student_id,
            name=name,
            issuer=data.get("issuer"),
        )
        db.session.add(c)
        db.session.commit()
        return {"id": c.id, "name": c.name}, None, 201

    @staticmethod
    def process_resume(student_id: int, file_obj, upload_dir_path: str) -> tuple[dict | None, str | None, int]:
        """Save, extract, and parse student resume file into structured skill evidence."""
        student = db.session.get(Student, student_id)
        if not student:
            return None, "student not found", 404

        if not file_obj:
            return None, "file is required (form field 'file' or 'resume')", 400

        ext = Path(file_obj.filename or "").suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            return None, f"Only PDF and DOCX files are supported. Got: {ext}", 400

        upload_dir = Path(upload_dir_path)
        upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = secure_filename(file_obj.filename or "resume")
        save_path = upload_dir / f"{student_id}_{safe_name}"
        file_obj.save(save_path)

        start_time = time.perf_counter()
        try:
            text = extract_text(str(save_path))
            mapped_skills, unknown_terms = extract_skills_with_evidence(text)
            projects = extract_projects_text(text)
            certs = extract_certifications_text(text)

            r = Resume(
                student_id=student_id,
                file_name=safe_name,
                stored_path=str(save_path),
                extracted_text=text,
                processing_status="processed",
            )
            db.session.add(r)
            db.session.flush()

            # 1. Persist granular skill evidence rows
            created_evidence = []
            for item in mapped_skills:
                ev = SkillEvidence(
                    student_id=student_id,
                    skill_id=item["skill_id"],
                    raw_term=item["skill"],
                    evidence_type="resume",
                    source_id=r.id,
                    confidence=item["confidence"],
                    evidence_span=item.get("evidence_span"),
                    section=item.get("section", "general"),
                    status="pending",
                )
                db.session.add(ev)
                created_evidence.append(ev)

            # 2. Persist unmapped skills to review queue
            for unk in unknown_terms:
                rev = UnknownSkillReview(
                    student_id=student_id,
                    raw_term=unk["raw_term"],
                    context_snippet=unk.get("context_snippet"),
                    source="resume",
                    status="pending_review",
                )
                db.session.add(rev)

            # 3. Persist AI extraction audit record
            latency_ms = (time.perf_counter() - start_time) * 1000.0
            word_count = len(text.split())
            audit = AIExtractionRecord(
                student_id=student_id,
                source_type="resume",
                source_id=r.id,
                model="rule-nlp-v1",
                prompt_version="v1.0",
                latency_ms=latency_ms,
                token_usage=word_count,
                skills_extracted_count=len(mapped_skills),
                unknown_count=len(unknown_terms),
            )
            db.session.add(audit)
            db.session.commit()

            return {
                "resume_id": r.id,
                "extracted_skills": mapped_skills,
                "extracted_projects": projects,
                "extracted_certs": certs,
                "unknown_terms_count": len(unknown_terms),
                "extraction_audit": audit.to_dict(),
                "message": (
                    "Review extracted skills and verify via "
                    "POST /api/v1/students/{id}/resume/verify"
                ),
            }, None, 201
        except Exception as exc:
            log.exception("Resume processing failed for student %s", student_id)
            return None, f"Resume processing failed: {exc}", 422

    @staticmethod
    def get_extracted_evidence(student_id: int, status_filter: str | None = None) -> tuple[list[dict] | None, str | None, int]:
        """Retrieve all skill evidence records for a student."""
        student = db.session.get(Student, student_id)
        if not student:
            return None, "student not found", 404

        query = SkillEvidence.query.filter_by(student_id=student_id)
        if status_filter:
            query = query.filter_by(status=status_filter)

        records = query.order_by(SkillEvidence.created_at.desc()).all()
        results = []
        for r in records:
            d = r.to_dict()
            if r.skill_id:
                skill = db.session.get(Skill, r.skill_id)
                d["canonical_skill_name"] = skill.name if skill else None
            results.append(d)
        return results, None, 200

    @staticmethod
    def verify_extracted_skills(student_id: int, verifications: list[dict]) -> tuple[dict | None, str | None, int]:
        """
        Verify or reject extracted skills from resume evidence.
        Accepted skills are persisted/updated in StudentSkill with evidence_type='resume'.
        """
        student = db.session.get(Student, student_id)
        if not student:
            return None, "student not found", 404

        if not verifications:
            return None, "verifications list is required", 400

        verified_count = 0
        rejected_count = 0

        for item in verifications:
            evidence_id = item.get("evidence_id")
            action = item.get("action")
            proficiency = float(item.get("proficiency", 50.0))

            if not evidence_id or action not in ("accept", "reject"):
                continue

            ev = SkillEvidence.query.filter_by(id=evidence_id, student_id=student_id).first()
            if not ev:
                continue

            if action == "accept":
                ev.status = "verified"
                verified_count += 1

                if ev.skill_id:
                    ss = StudentSkill.query.filter_by(
                        student_id=student_id, skill_id=ev.skill_id
                    ).first()
                    if ss:
                        ss.proficiency = max(ss.proficiency, proficiency)
                        ss.evidence_type = "resume"
                        ss.confidence = 0.85
                        ss.updated_at = _utcnow()
                    else:
                        ss = StudentSkill(
                            student_id=student_id,
                            skill_id=ev.skill_id,
                            proficiency=proficiency,
                            evidence_type="resume",
                            confidence=0.85,
                            updated_at=_utcnow(),
                        )
                        db.session.add(ss)

            elif action == "reject":
                ev.status = "rejected"
                rejected_count += 1

        db.session.commit()
        _cache.invalidate_student(student_id)

        return {
            "verified_count": verified_count,
            "rejected_count": rejected_count,
            "message": f"Successfully verified {verified_count} and rejected {rejected_count} skills.",
        }, None, 200

    @staticmethod
    def get_unknown_skills(student_id: int) -> tuple[list[dict] | None, str | None, int]:
        """Retrieve unknown candidate terms pending review for a student."""
        student = db.session.get(Student, student_id)
        if not student:
            return None, "student not found", 404

        reviews = UnknownSkillReview.query.filter_by(student_id=student_id).all()
        return [r.to_dict() for r in reviews], None, 200

    @staticmethod
    def get_extraction_records(student_id: int) -> tuple[list[dict] | None, str | None, int]:
        """Retrieve AI extraction audit history for a student."""
        student = db.session.get(Student, student_id)
        if not student:
            return None, "student not found", 404

        records = AIExtractionRecord.query.filter_by(student_id=student_id).order_by(AIExtractionRecord.created_at.desc()).all()
        return [r.to_dict() for r in records], None, 200

