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
    Returns a list of candidate skill dicts with confidence and evidence type.
    Uses app context to query the Skill table.
    """
    from models import Skill
    lower = normalize_text(text)

    # Build a lookup: normalized_name → canonical Skill
    skills = Skill.query.all()
    found: dict[int, dict] = {}   # skill_id → result dict

    def _check(pattern: str, skill: "Skill", confidence: float):
        # Whole-word match with word boundary awareness
        pat = r"(?<![a-z0-9\+\#])" + re.escape(pattern.lower()) + r"(?![a-z0-9\+\#])"
        if re.search(pat, lower):
            if skill.id not in found:
                found[skill.id] = {
                    "skill_id": skill.id,
                    "skill": skill.name,
                    "confidence": confidence,
                    "evidence": "resume_keyword_match"
                }

    for s in skills:
        _check(s.name, s, 0.85)

    # Also match aliases → look up canonical Skill by name
    for alias, canonical_name in SKILL_ALIASES.items():
        canonical = Skill.query.filter(
            db.func.lower(Skill.name) == canonical_name.lower()
        ).first()
        if canonical and canonical.id not in found:
            _check(alias, canonical, 0.75)

    return list(found.values())


# ─────────────────────────────────────────────────────────────────────────────
# Section Extraction (Projects / Certifications)
# ─────────────────────────────────────────────────────────────────────────────
SECTION_HEADERS = {
    "projects": re.compile(
        r"^\s*(projects?|academic projects?|personal projects?|side projects?)\s*$",
        re.IGNORECASE | re.MULTILINE
    ),
    "certifications": re.compile(
        r"^\s*(certifications?|licenses?|courses? completed|achievements?)\s*$",
        re.IGNORECASE | re.MULTILINE
    ),
}

_NEXT_SECTION = re.compile(
    r"^\s*(experience|education|skills?|summary|objective|references?|"
    r"awards?|projects?|certifications?|activities)\s*$",
    re.IGNORECASE | re.MULTILINE
)


def _extract_section_text(text: str, section_pattern: re.Pattern) -> str:
    """Extract text between section header and next section header."""
    m = section_pattern.search(text)
    if not m:
        return ""
    start = m.end()
    rest = text[start:]
    # Find next section boundary
    next_m = _NEXT_SECTION.search(rest)
    end = next_m.start() if next_m else len(rest)
    return rest[:end].strip()


def extract_projects_text(text: str) -> list[str]:
    """Return a list of project title/description strings from the resume."""
    section = _extract_section_text(text, SECTION_HEADERS["projects"])
    if not section:
        return []
    lines = [l.strip() for l in section.split("\n") if l.strip()]
    # Filter out very short lines (bullets) — keep descriptive ones
    return [l for l in lines if len(l) > 15][:10]


def extract_certifications_text(text: str) -> list[str]:
    """Return a list of certification/course names from the resume."""
    section = _extract_section_text(text, SECTION_HEADERS["certifications"])
    if not section:
        return []
    lines = [l.strip() for l in section.split("\n") if l.strip()]
    return [l for l in lines if len(l) > 5][:10]
