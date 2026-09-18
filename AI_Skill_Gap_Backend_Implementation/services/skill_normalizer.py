"""
services/skill_normalizer.py — Canonicalization and equivalence engine for skills.

Provides:
  1. canonicalize_skill_name(raw: str) -> str:
     Maps variations, version suffixes, and sub-skills (e.g. 'css', 'css3', 'css5',
     'flexbox', 'box css', 'css grid') to a single canonical skill name ('CSS3').

  2. get_equivalent_skill_ids(target_skill_id: int) -> list[int]:
     Finds all skill IDs in the database that belong to the same equivalence family,
     allowing GapEngine and RoleMatcher to give students credit even if they entered
     a synonym or sub-skill under another skill record.
"""
from __future__ import annotations
import re
from extensions import db
from models import Skill

# ─────────────────────────────────────────────────────────────────────────────
# Canonical Alias & Synonym Dictionary
# Maps lowercased, punctuation-cleaned query keys to canonical skill names.
# ─────────────────────────────────────────────────────────────────────────────
SKILL_ALIAS_MAP: dict[str, str] = {
    # CSS & Layout Family
    "css": "CSS3",
    "css3": "CSS3",
    "css 3": "CSS3",
    "css5": "CSS3",
    "css 5": "CSS3",
    "box css": "CSS3",
    "css box": "CSS3",
    "css box model": "CSS3",
    "flexbox": "CSS3",
    "css flexbox": "CSS3",
    "css grid": "CSS3",
    "grid css": "CSS3",
    "cascading style sheets": "CSS3",
    "styling": "CSS3",
    "flexbox / css grid": "CSS3",

    # HTML & Web Semantics
    "html": "HTML5",
    "html5": "HTML5",
    "html 5": "HTML5",
    "xhtml": "HTML5",
    "semantic html": "HTML5",
    "html semantics": "HTML5",

    # JavaScript Family
    "js": "JavaScript",
    "javascript": "JavaScript",
    "ecmascript": "JavaScript",
    "es6": "JavaScript",
    "es2015": "JavaScript",
    "es2020": "JavaScript",
    "vanilla js": "JavaScript",
    "modern javascript": "JavaScript",

    # TypeScript
    "ts": "TypeScript",
    "typescript": "TypeScript",

    # React
    "react": "React",
    "reactjs": "React",
    "react.js": "React",
    "react / vue": "React",

    # Node.js
    "node": "Node.js",
    "nodejs": "Node.js",
    "node.js": "Node.js",

    # Python
    "py": "Python",
    "python": "Python",
    "python3": "Python",
    "python 3": "Python",
    "python 2": "Python",
    "py3": "Python",

    # Java
    "java": "Java",
    "core java": "Java",
    "java / android": "Java / Android",
    "android java": "Java / Android",

    # C++ & OOP
    "c++": "C++ / OOP",
    "cpp": "C++ / OOP",
    "c plus plus": "C++ / OOP",
    "c++/oop": "C++ / OOP",
    "c++ / oop": "C++ / OOP",
    "oop": "C++ / OOP",
    "object oriented programming": "C++ / OOP",

    # SQL & Databases
    "sql": "SQL",
    "mysql": "MySQL Administration",
    "mysql administration": "MySQL Administration",
    "mysql db": "MySQL Administration",
    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",
    "postgres administration": "PostgreSQL Administration",
    "postgresql administration": "PostgreSQL Administration",
    "postgresql / mysql": "PostgreSQL / MySQL",
    "rdbms": "SQL",
    "relational database": "SQL",
    "sqlite": "SQLite",
    "mongo": "MongoDB",
    "mongodb": "MongoDB",

    # REST APIs
    "rest": "REST APIs",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "restful": "REST APIs",
    "restful api": "REST APIs",
    "restful apis": "REST APIs",
    "rest api development": "REST API Development",
    "rest api concepts": "REST API Concepts",
    "rest api integration": "REST API Integration",

    # Git & Version Control
    "git": "Git",
    "github": "Git",
    "gitlab": "Git",
    "version control": "Git",
    "git version control": "Git",

    # Docker & Containers
    "docker": "Docker",
    "docker container": "Docker",
    "docker containers": "Docker",
    "containerization": "Docker",
    "containers": "Docker",

    # Kubernetes
    "k8s": "Kubernetes",
    "kubernetes": "Kubernetes",
    "kube": "Kubernetes",

    # Cloud
    "aws": "AWS / Azure / GCP",
    "azure": "AWS / Azure / GCP",
    "gcp": "AWS / Azure / GCP",
    "amazon web services": "AWS / Azure / GCP",
    "google cloud platform": "AWS / Azure / GCP",
    "microsoft azure": "AWS / Azure / GCP",
    "aws / azure / gcp": "AWS / Azure / GCP",

    # Linux & OS
    "linux": "Linux Administration",
    "linux admin": "Linux Administration",
    "linux administration": "Linux Administration",
    "linux / shell scripting": "Linux / Shell Scripting",
    "bash": "Bash Scripting",
    "bash scripting": "Bash Scripting",
    "shell scripting": "Bash Scripting",
    "shell": "Bash Scripting",

    # Data Science & ML
    "ml": "Machine Learning",
    "machine learning": "Machine Learning",
    "machine learning algorithms": "Machine Learning",
    "dl": "Deep Learning",
    "deep learning": "Deep Learning",
    "nlp": "NLP Fundamentals",
    "nlp fundamentals": "NLP Fundamentals",
    "natural language processing": "NLP Fundamentals",
    "cv": "NLP / Computer Vision",
    "computer vision": "NLP / Computer Vision",
    "scikit": "Scikit-learn",
    "scikit-learn": "Scikit-learn",
    "sklearn": "Scikit-learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "tensorflow": "TensorFlow",
    "tf": "TensorFlow",

    # CI/CD
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "continuous integration": "CI/CD",
    "github actions": "CI/CD",
    "jenkins": "CI/CD",

    # Testing
    "testing": "Software Testing Fundamentals",
    "software testing": "Software Testing Fundamentals",
    "software testing fundamentals": "Software Testing Fundamentals",
    "unit test": "Unit Testing",
    "unit testing": "Unit Testing",
    "qa": "Manual Testing",
    "manual testing": "Manual Testing",
    "api testing": "API Testing",
    "selenium": "Selenium",
    "cypress": "Playwright / Cypress",
    "playwright": "Playwright / Cypress",
    "playwright / cypress": "Playwright / Cypress",

    # Frontend UI
    "tailwind": "Tailwind CSS / UI Libraries",
    "tailwind css": "Tailwind CSS / UI Libraries",
    "tailwindcss": "Tailwind CSS / UI Libraries",
    "responsive design": "Responsive Web Design",
    "responsive web design": "Responsive Web Design",
    "accessibility": "Web Accessibility",
    "web accessibility": "Web Accessibility",
    "wcag": "WCAG Accessibility",
    "wcag accessibility": "WCAG Accessibility",
}

# Reverse family clusters: canonical name -> set of equivalent/sub-skill names
EQUIVALENCE_FAMILIES: dict[str, set[str]] = {}
for alias, canon in SKILL_ALIAS_MAP.items():
    EQUIVALENCE_FAMILIES.setdefault(canon.lower(), set()).add(alias.lower())
    EQUIVALENCE_FAMILIES[canon.lower()].add(canon.lower())


def clean_skill_str(raw: str) -> str:
    """Normalize raw string by removing excess whitespace, brackets, and extra punctuation."""
    if not raw:
        return ""
    s = raw.strip()
    s = re.sub(r"\s+", " ", s)
    return s


def canonicalize_skill_name(raw_name: str) -> str:
    """
    Map an input skill string to its canonical taxonomy name.
    If no alias is known, returns cleaned original casing.

    Examples:
        'css'         -> 'CSS3'
        'css5'        -> 'CSS3'
        'flexbox'     -> 'CSS3'
        'box css'     -> 'CSS3'
        'js'          -> 'JavaScript'
        'html'        -> 'HTML5'
        'postgres'    -> 'PostgreSQL'
        'k8s'         -> 'Kubernetes'
    """
    cleaned = clean_skill_str(raw_name)
    if not cleaned:
        return ""

    key = cleaned.lower()

    # Exact alias dictionary lookup
    if key in SKILL_ALIAS_MAP:
        return SKILL_ALIAS_MAP[key]

    # Handle version suffixes like 'css 4', 'python 3.9'
    css_match = re.match(r"^css\s*\d*$", key)
    if css_match:
        return "CSS3"

    html_match = re.match(r"^html\s*\d*$", key)
    if html_match:
        return "HTML5"

    python_match = re.match(r"^python\s*\d+(\.\d+)?$", key)
    if python_match:
        return "Python"

    return cleaned


def get_equivalent_skill_ids(target_skill_id: int) -> list[int]:
    """
    Return all skill IDs in the database that are equivalent to `target_skill_id`.
    Includes `target_skill_id` itself, plus any existing database skills whose
    names map to the same equivalence family.

    Ensures that if a student has proficiency in 'CSS', 'Flexbox', or 'CSS3',
    they receive credit for 'CSS3' requirement during gap analysis.
    """
    base_skill = db.session.get(Skill, target_skill_id)
    if not base_skill:
        return [target_skill_id]

    canon = canonicalize_skill_name(base_skill.name).lower()
    family_names = EQUIVALENCE_FAMILIES.get(canon, {canon, base_skill.name.lower()})

    matching_skills = Skill.query.filter(
        db.func.lower(Skill.name).in_(family_names)
    ).all()

    ids = {target_skill_id}
    for s in matching_skills:
        ids.add(s.id)

    return list(ids)


def layered_skill_lookup(
    raw_term: str,
    min_fuzzy_ratio: float = 0.82
) -> tuple[Skill | None, str, float]:
    """
    Multi-layer normalization pipeline to map raw terms to canonical catalog skills:
      Layer 1: Exact case-insensitive match against Skill.name (confidence 1.0)
      Layer 2: Alias dictionary match via SKILL_ALIAS_MAP (confidence 0.90)
      Layer 3: Canonicalized name exact match in DB (confidence 0.88)
      Layer 4: Fuzzy string match (difflib SequenceMatcher >= min_fuzzy_ratio) (confidence 0.75–0.85)
      Layer 5: Token containment / word boundary match against canonical catalog (confidence 0.72)
      Layer 6: Unknown — returns (None, "unknown", 0.0) for routing to review queue.

    Returns:
      (matched_skill, match_layer, confidence)
    """
    import difflib

    cleaned = clean_skill_str(raw_term)
    if not cleaned:
        return None, "empty", 0.0

    lower_cleaned = cleaned.lower()

    # Layer 1: Exact match against canonical database skill name
    exact = Skill.query.filter(db.func.lower(Skill.name) == lower_cleaned).first()
    if exact:
        return exact, "exact", 1.0

    # Layer 2: Alias lookup
    if lower_cleaned in SKILL_ALIAS_MAP:
        alias_target = SKILL_ALIAS_MAP[lower_cleaned]
        matched = Skill.query.filter(db.func.lower(Skill.name) == alias_target.lower()).first()
        if matched:
            return matched, "alias", 0.90

    # Layer 3: Rule-based canonicalization
    canon_name = canonicalize_skill_name(cleaned)
    if canon_name.lower() != lower_cleaned:
        canon_match = Skill.query.filter(db.func.lower(Skill.name) == canon_name.lower()).first()
        if canon_match:
            return canon_match, "canonical_rule", 0.88

    # Pre-fetch all skills for Layer 4 & Layer 5
    all_skills = Skill.query.all()
    if not all_skills:
        return None, "unknown", 0.0

    # Layer 4: Fuzzy matching
    best_skill: Skill | None = None
    best_ratio: float = 0.0
    for s in all_skills:
        s_lower = s.name.lower()
        ratio = difflib.SequenceMatcher(None, lower_cleaned, s_lower).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_skill = s

    if best_ratio >= min_fuzzy_ratio and best_skill:
        confidence = round(0.75 + (best_ratio - min_fuzzy_ratio) * 0.5, 2)
        return best_skill, "fuzzy", min(0.85, confidence)

    # Layer 5: Token containment / boundary matching
    for s in all_skills:
        s_lower = s.name.lower()
        # Word boundary check
        pattern_1 = r"(?<![a-z0-9])" + re.escape(lower_cleaned) + r"(?![a-z0-9])"
        pattern_2 = r"(?<![a-z0-9])" + re.escape(s_lower) + r"(?![a-z0-9])"
        if re.search(pattern_1, s_lower) or re.search(pattern_2, lower_cleaned):
            return s, "token_containment", 0.72

    # Layer 6: Unknown — unmapped term
    return None, "unknown", 0.0

