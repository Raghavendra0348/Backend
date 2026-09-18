"""
services/resume_parser.py — PDF/DOCX text extraction and NLP candidate skill extraction.

Pipeline:
  File → text extraction → text normalization → candidate skill matching
       → confidence scoring → section extraction (projects/certs) → return
"""
from extensions import db
import re
from pathlib import Path

from pypdf import PdfReader
from docx import Document


# ─────────────────────────────────────────────────────────────────────────────
# Text Extraction
# ─────────────────────────────────────────────────────────────────────────────
def extract_text(path: str) -> str:
    """
    Extract plain text from a PDF or DOCX file.
    Raises ValueError for unsupported extensions.
    """
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        pages = []
        try:
            reader = PdfReader(path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        except Exception as e:
            raise ValueError(f"Failed to read PDF: {e}") from e
        return "\n".join(pages)

    if ext == ".docx":
        try:
            doc = Document(path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n".join(paragraphs)
        except Exception as e:
            raise ValueError(f"Failed to read DOCX: {e}") from e

    raise ValueError(f"Unsupported file type '{ext}'. Only PDF and DOCX are supported.")


# ─────────────────────────────────────────────────────────────────────────────
# Text Normalisation
# ─────────────────────────────────────────────────────────────────────────────
def normalize_text(text: str) -> str:
    """Lower-case, collapse whitespace, strip special characters except useful ones."""
    text = text.lower()
    text = re.sub(r"[^\w\s\+\#\.\-/]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


# ─────────────────────────────────────────────────────────────────────────────
# Candidate Skill Matching
# ─────────────────────────────────────────────────────────────────────────────
# Alias map: resume keywords → canonical skill names
SKILL_ALIASES: dict[str, str] = {
    "py":                    "Python",
    "python3":               "Python",
    "python 3":              "Python",
    "machine learning":      "Machine Learning",
    "ml":                    "Machine Learning",
    "deep learning":         "Deep Learning",
    "dl":                    "Deep Learning",
    "natural language processing": "NLP",
    "rest api":              "REST API",
    "restful api":           "REST API",
    "restful":               "REST API",
    "sql server":            "SQL",
    "mysql":                 "MySQL",
    "postgresql":            "PostgreSQL",
    "postgres":              "PostgreSQL",
    "mongodb":               "MongoDB",
    "nosql":                 "MongoDB",
    "js":                    "JavaScript",
    "node.js":               "Node.js",
    "nodejs":                "Node.js",
    "react.js":              "React",
    "reactjs":               "React",
    "angular.js":            "Angular",
    "angularjs":             "Angular",
    "c programming":         "C",
    "c++ programming":       "C++",
    "object oriented":       "Object-Oriented Programming",
    "oop":                   "Object-Oriented Programming",
    "version control":       "Git",
    "software testing":      "Software Testing",
    "unit testing":          "Software Testing",
    "test driven":           "Software Testing",
    "docker container":      "Docker",
    "kubernetes":            "Kubernetes",
    "k8s":                   "Kubernetes",
    "amazon web services":   "AWS",
    "google cloud":          "GCP",
    "google cloud platform": "GCP",
    "microsoft azure":       "Azure",
    "agile methodology":     "Agile",
    "scrum methodology":     "Scrum",
    "data analysis":         "Data Analysis",
    "data visualization":    "Data Visualization",
    "data structures and algorithms": "Algorithms & Data Structures",
    "algorithms and data structures": "Algorithms & Data Structures",
    "dsa":                   "Algorithms & Data Structures",
}


def candidate_skills(text: str) -> list[dict]:
    """
    Match canonical skill vocabulary against normalized resume text.
    Returns a list of candidate skill dicts with confidence, evidence type, evidence_span, and section.
    """
    mapped, _ = extract_skills_with_evidence(text)
    return mapped


# ─────────────────────────────────────────────────────────────────────────────
# Section Extraction & Evidenced Extraction Pipeline
# ─────────────────────────────────────────────────────────────────────────────
SECTION_HEADERS = {
    "skills": re.compile(
        r"^\s*(skills?|technical skills?|technologies|competencies|core competencies|tools & technologies)\s*$",
        re.IGNORECASE | re.MULTILINE
    ),
    "experience": re.compile(
        r"^\s*(experience|work experience|professional experience|employment|internships?)\s*$",
        re.IGNORECASE | re.MULTILINE
    ),
    "projects": re.compile(
        r"^\s*(projects?|academic projects?|personal projects?|side projects?|key projects?)\s*$",
        re.IGNORECASE | re.MULTILINE
    ),
    "certifications": re.compile(
        r"^\s*(certifications?|licenses?|courses? completed|achievements?)\s*$",
        re.IGNORECASE | re.MULTILINE
    ),
    "education": re.compile(
        r"^\s*(education|academics?|academic background|qualifications?)\s*$",
        re.IGNORECASE | re.MULTILINE
    ),
}

_ALL_HEADERS = re.compile(
    r"^\s*(experience|work experience|professional experience|employment|internships?|"
    r"education|academics?|academic background|qualifications?|"
    r"skills?|technical skills?|technologies|competencies|core competencies|tools & technologies|"
    r"summary|objective|profile|references?|awards?|"
    r"projects?|academic projects?|personal projects?|side projects?|key projects?|"
    r"certifications?|licenses?|courses? completed|achievements?|activities)\s*$",
    re.IGNORECASE | re.MULTILINE
)


def split_resume_into_sections(text: str) -> dict[str, str]:
    """
    Partition resume text into recognized sections.
    Returns mapping: section_name -> section_body_text.
    """
    sections: dict[str, str] = {"general": ""}
    matches = list(_ALL_HEADERS.finditer(text))

    if not matches:
        sections["general"] = text
        return sections

    # Leading text before first recognized header
    if matches[0].start() > 0:
        sections["general"] = text[:matches[0].start()].strip()

    for idx, match in enumerate(matches):
        header_text = match.group(0).strip().lower()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        content = text[start:end].strip()

        # Identify which normalized section category this header belongs to
        category = "general"
        for sec_name, pat in SECTION_HEADERS.items():
            if pat.match(header_text):
                category = sec_name
                break

        if category in sections and sections[category]:
            sections[category] += "\n" + content
        else:
            sections[category] = content

    return sections


def _extract_evidence_span(text: str, keyword: str, max_chars: int = 180) -> str:
    """Find the sentence or line containing the keyword to provide clear context."""
    pat = r"(?<![a-z0-9\+\#])" + re.escape(keyword.lower()) + r"(?![a-z0-9\+\#])"
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines:
        if re.search(pat, line.lower()):
            clean = " ".join(line.split())
            return clean[:max_chars]
    return f"Mentioned in resume: {keyword}"


def extract_skills_with_evidence(text: str) -> tuple[list[dict], list[dict]]:
    """
    Extract skills with section attribution, evidence spans, confidence scoring,
    and unknown skill detection for review.

    Returns:
        (mapped_skills, unknown_terms)
    """
    from models import Skill
    from services.skill_normalizer import layered_skill_lookup

    if not text or not text.strip():
        return [], []

    sections = split_resume_into_sections(text)
    all_skills = Skill.query.all()
    found_skills: dict[int, dict] = {}   # skill_id -> skill dict
    unknown_terms_dict: dict[str, dict] = {}

    # Section confidence adjustments
    section_bonus = {
        "projects": 0.08,
        "experience": 0.08,
        "skills": 0.05,
        "certifications": 0.05,
        "education": 0.0,
        "general": 0.0,
    }

    # 1. Match canonical skills across all sections
    for sec_name, sec_text in sections.items():
        if not sec_text:
            continue
        sec_lower = normalize_text(sec_text)
        bonus = section_bonus.get(sec_name, 0.0)

        for s in all_skills:
            pat = r"(?<![a-z0-9\+\#])" + re.escape(s.name.lower()) + r"(?![a-z0-9\+\#])"
            if re.search(pat, sec_lower):
                span = _extract_evidence_span(sec_text, s.name)
                conf = min(0.98, round(0.85 + bonus, 2))
                if s.id not in found_skills or conf > found_skills[s.id]["confidence"]:
                    found_skills[s.id] = {
                        "skill_id": s.id,
                        "skill": s.name,
                        "confidence": conf,
                        "evidence": "resume_keyword_match",
                        "evidence_span": span,
                        "section": sec_name,
                        "match_layer": "exact",
                    }

        # 2. Match aliases across sections
        for alias, canon_name in SKILL_ALIASES.items():
            pat = r"(?<![a-z0-9\+\#])" + re.escape(alias.lower()) + r"(?![a-z0-9\+\#])"
            if re.search(pat, sec_lower):
                canonical = Skill.query.filter(
                    db.func.lower(Skill.name) == canon_name.lower()
                ).first()
                if canonical:
                    span = _extract_evidence_span(sec_text, alias)
                    conf = min(0.95, round(0.75 + bonus, 2))
                    if canonical.id not in found_skills or conf > found_skills[canonical.id]["confidence"]:
                        found_skills[canonical.id] = {
                            "skill_id": canonical.id,
                            "skill": canonical.name,
                            "confidence": conf,
                            "evidence": "resume_alias_match",
                            "evidence_span": span,
                            "section": sec_name,
                            "match_layer": "alias",
                        }

    # 3. Analyze candidate terms from the "skills" section for layered lookup & unknown review queue
    skills_section = sections.get("skills", "")
    if skills_section:
        # Split by commas, bullets, pipes, slashes, or newlines
        tokens = re.split(r"[,;\|\n•\-\*]+", skills_section)
        for tok in tokens:
            cleaned = tok.strip()
            # Filter out very short or overly long tokens
            if len(cleaned) < 2 or len(cleaned) > 50:
                continue
            if re.match(r"^\d+$", cleaned):
                continue

            matched_skill, match_layer, conf = layered_skill_lookup(cleaned)
            if matched_skill:
                if matched_skill.id not in found_skills:
                    found_skills[matched_skill.id] = {
                        "skill_id": matched_skill.id,
                        "skill": matched_skill.name,
                        "confidence": min(0.95, conf),
                        "evidence": f"resume_{match_layer}_match",
                        "evidence_span": _extract_evidence_span(skills_section, cleaned),
                        "section": "skills",
                        "match_layer": match_layer,
                    }
            else:
                # Potential candidate term not found in canonical catalog -> route to unknown review
                lower_term = cleaned.lower()
                # Exclude trivial non-skill words
                if lower_term not in {"and", "with", "other", "proficient", "familiar", "knowledge", "tools", "languages"}:
                    if lower_term not in unknown_terms_dict:
                        unknown_terms_dict[lower_term] = {
                            "raw_term": cleaned,
                            "context_snippet": _extract_evidence_span(skills_section, cleaned),
                            "section": "skills",
                            "confidence": 0.50,
                        }

    return list(found_skills.values()), list(unknown_terms_dict.values())


def _extract_section_text(text: str, section_pattern: re.Pattern) -> str:
    """Extract text between section header and next section header."""
    m = section_pattern.search(text)
    if not m:
        return ""
    start = m.end()
    rest = text[start:]
    next_m = _ALL_HEADERS.search(rest)
    end = next_m.start() if next_m else len(rest)
    return rest[:end].strip()


def extract_projects_text(text: str) -> list[str]:
    """Return a list of project title/description strings from the resume."""
    section = _extract_section_text(text, SECTION_HEADERS["projects"])
    if not section:
        return []
    lines = [l.strip() for l in section.split("\n") if l.strip()]
    return [l for l in lines if len(l) > 15][:10]


def extract_certifications_text(text: str) -> list[str]:
    """Return a list of certification/course names from the resume."""
    section = _extract_section_text(text, SECTION_HEADERS["certifications"])
    if not section:
        return []
    lines = [l.strip() for l in section.split("\n") if l.strip()]
    return [l for l in lines if len(l) > 5][:10]

