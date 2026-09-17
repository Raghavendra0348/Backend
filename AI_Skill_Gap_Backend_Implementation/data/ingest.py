"""
data/ingest.py — ETL pipeline for ESCO v1.2.1, O*NET, Coursera, and Student datasets.

Run via Flask CLI:
    flask --app app ingest-data

This populates:
    - job_roles      (from ESCO)
    - skills         (canonical vocabulary from ESCO + IT-specific additions)
    - job_skills     (ESCO occupation-skill relations for IT roles)
    - courses        (from Coursera.csv in the Dataset archive)
    - course_skills  (mapped from Coursera "Skills" column)
    - students       (sample from Indian names student dataset)
    - student_skills (from student dataset "technical_skills" + "rating" columns)
"""
import csv
import io
import os
import re
import zipfile
from pathlib import Path
from flask import current_app

from extensions import db
from models import (
    JobRole, Skill, JobSkill, Course, CourseSkill, Student, StudentSkill
)

# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Definitive 15 IT Roles × 15 Core Skills Taxonomy (Dual Taxonomy: ESCO + O*NET)
# ─────────────────────────────────────────────────────────────────────────────

TAXONOMY_15_ROLES = {
    "Web Developer": {
        "esco_uri": "http://data.europa.eu/esco/occupation/9d44fa85-9f5b-426b-80df-596908e2f89f",
        "isco_group": "2513",
        "onet_code": "15-1254.00",
        "description": "Web developers build, format, design, and maintain user-facing websites, web applications, and web services using front-end and back-end web standards.",
        "essential_skills": [
            "HTML5", "CSS3", "JavaScript", "TypeScript", "React",
            "Node.js", "REST APIs", "SQL", "Git", "Responsive Web Design"
        ],
        "optional_skills": [
            "Web Accessibility", "Web Security / OWASP", "Browser DevTools",
            "Web Performance Optimization", "Web Testing"
        ],
        "skills": [
            "HTML5", "CSS3", "JavaScript", "TypeScript", "React",
            "Node.js", "REST APIs", "SQL", "Git", "Responsive Web Design",
            "Web Accessibility", "Web Security / OWASP", "Browser DevTools",
            "Web Performance Optimization", "Web Testing"
        ]
    },
    "Software Developer": {
        "esco_uri": "http://data.europa.eu/esco/occupation/f2b15a0e-e65a-438a-affb-29b9d50b77d1",
        "isco_group": "2512",
        "onet_code": "15-1252.00",
        "description": "Software developers analyze requirements, design software systems, write high-quality code, test programs, and maintain applications.",
        "essential_skills": [
            "Python", "Java", "Data Structures & Algorithms", "SQL", "Git",
            "REST API Development", "Docker", "Linux / Shell Scripting",
            "Unit Testing", "Software Architecture"
        ],
        "optional_skills": [
            "C++ / OOP", "Design Patterns", "CI/CD", "Agile / Scrum", "Debugging & Profiling"
        ],
        "skills": [
            "Python", "Java", "C++ / OOP", "Data Structures & Algorithms", "SQL",
            "Git", "REST API Development", "Docker", "Linux / Shell Scripting",
            "Unit Testing", "Software Architecture", "Design Patterns", "CI/CD",
            "Agile / Scrum", "Debugging & Profiling"
        ]
    },
    "Data Scientist": {
        "esco_uri": "http://data.europa.eu/esco/occupation/2079755f-d809-49e6-8037-4de6180e54c0",
        "isco_group": "2511",
        "onet_code": "15-2051.00",
        "description": "Data scientists find and interpret complex data patterns, build statistical models, design machine learning algorithms, and derive predictive insights.",
        "essential_skills": [
            "Python", "SQL", "Pandas", "NumPy", "Scikit-learn",
            "Statistics", "Probability", "Data Cleaning", "Feature Engineering",
            "Machine Learning"
        ],
        "optional_skills": [
            "Model Evaluation", "Data Visualization", "NLP Fundamentals",
            "Apache Spark", "MLOps Fundamentals"
        ],
        "skills": [
            "Python", "SQL", "Pandas", "NumPy", "Scikit-learn",
            "Statistics", "Probability", "Data Cleaning", "Feature Engineering",
            "Machine Learning", "Model Evaluation", "Data Visualization",
            "NLP Fundamentals", "Apache Spark", "MLOps Fundamentals"
        ]
    },
    "Cloud / DevOps Engineer": {
        "esco_uri": "http://data.europa.eu/esco/occupation/1a4739eb-e36b-4e0e-88ad-6f29630cff3b",
        "isco_group": "2512",
        "onet_code": "15-1241.00",
        "description": "Cloud DevOps engineers bridge software development and operations by automating CI/CD pipelines, provisioning infrastructure as code, and managing cloud environments.",
        "essential_skills": [
            "Linux Administration", "Bash Scripting", "Docker", "Kubernetes",
            "AWS / Azure / GCP", "Terraform", "Infrastructure as Code", "CI/CD",
            "Git", "Cloud IAM"
        ],
        "optional_skills": [
            "Python Automation", "TCP/IP Networking", "Monitoring & Observability",
            "Logging", "SRE Fundamentals"
        ],
        "skills": [
            "Linux Administration", "Bash Scripting", "Docker", "Kubernetes",
            "AWS / Azure / GCP", "Terraform", "Infrastructure as Code", "CI/CD",
            "Git", "Python Automation", "TCP/IP Networking", "Cloud IAM",
            "Monitoring & Observability", "Logging", "SRE Fundamentals"
        ]
    },
    "Database Administrator": {
        "esco_uri": "http://data.europa.eu/esco/occupation/8e040a43-855f-4a0b-8d07-73bcf3d6a6ef",
        "isco_group": "2521",
        "onet_code": "15-1242.00",
        "description": "Database administrators design, deploy, maintain, optimize, secure, and troubleshoot enterprise relational and distributed database systems.",
        "essential_skills": [
            "SQL", "PostgreSQL Administration", "MySQL Administration",
            "Database Schema Design", "Database Normalization", "Query Optimization",
            "Indexing", "Backup & Recovery", "Database Security", "Linux Administration"
        ],
        "optional_skills": [
            "Database Performance Monitoring", "Disaster Recovery", "Replication",
            "High Availability", "Database Migration"
        ],
        "skills": [
            "SQL", "PostgreSQL Administration", "MySQL Administration",
            "Database Schema Design", "Database Normalization", "Query Optimization",
            "Indexing", "Database Performance Monitoring", "Backup & Recovery",
            "Disaster Recovery", "Database Security", "Replication",
            "High Availability", "Database Migration", "Linux Administration"
        ]
    },
    "ICT System Analyst": {
        "esco_uri": "http://data.europa.eu/esco/occupation/0e286591-2a6d-495e-9a2e-ffbaef0b9df2",
        "isco_group": "2511",
        "onet_code": "15-1211.00",
        "description": "ICT system analysts specify, design, and evaluate technical solutions to satisfy business and organizational requirements.",
        "essential_skills": [
            "Requirements Engineering", "Requirements Analysis", "System Modeling",
            "Business Process Modeling", "Gap Analysis", "SQL", "REST API Concepts",
            "System Integration", "Agile / Scrum", "Technical Documentation"
        ],
        "optional_skills": [
            "UML", "Software Architecture Analysis", "Functional Testing",
            "User Acceptance Testing", "User Stories"
        ],
        "skills": [
            "Requirements Engineering", "Requirements Analysis", "UML",
            "System Modeling", "Business Process Modeling", "Gap Analysis",
            "SQL", "REST API Concepts", "System Integration",
            "Software Architecture Analysis", "Functional Testing",
            "User Acceptance Testing", "Agile / Scrum", "User Stories",
            "Technical Documentation"
        ]
    },
    "Mobile Application Developer": {
        "esco_uri": "http://data.europa.eu/esco/occupation/59da3142-2b21-4f18-b2ef-3759ad33eaad",
        "isco_group": "2514",
        "onet_code": "15-1255.00",
        "description": "Mobile application developers architect, build, optimize, and publish native and cross-platform applications for iOS and Android devices.",
        "essential_skills": [
            "Kotlin", "Java / Android", "Swift / iOS", "React Native",
            "REST API Integration", "JSON / API Communication", "SQLite",
            "Mobile UI/UX", "Mobile State Management", "App Store / Google Play Deployment"
        ],
        "optional_skills": [
            "Flutter", "Material Design", "Push Notifications",
            "Mobile Security", "Mobile Testing"
        ],
        "skills": [
            "Kotlin", "Java / Android", "Swift / iOS", "Flutter",
            "React Native", "Mobile UI/UX", "Material Design",
            "REST API Integration", "JSON / API Communication", "SQLite",
            "Mobile State Management", "Push Notifications", "Mobile Security",
            "Mobile Testing", "App Store / Google Play Deployment"
        ]
    },
    "UI / Frontend Developer": {
        "esco_uri": "http://data.europa.eu/esco/occupation/4c0c1694-b26a-4d22-b5e1-eb11f59235a9",
        "isco_group": "2512",
        "onet_code": "15-1255.00",
        "description": "UI / Frontend developers translate UI/UX designs into accessible, performant, responsive, and interactive graphical web interfaces.",
        "essential_skills": [
            "HTML5", "CSS3", "JavaScript", "TypeScript", "React",
            "Tailwind CSS / UI Libraries", "Responsive Design", "State Management",
            "Design Systems", "Frontend Performance"
        ],
        "optional_skills": [
            "Mobile-First Development", "WCAG Accessibility", "Figma-to-Code",
            "Browser DevTools", "Web Testing"
        ],
        "skills": [
            "HTML5", "CSS3", "JavaScript", "TypeScript", "React",
            "Tailwind CSS / UI Libraries", "Responsive Design", "State Management",
            "Design Systems", "Frontend Performance",
            "Mobile-First Development", "WCAG Accessibility", "Figma-to-Code",
            "Browser DevTools", "Web Testing"
        ]
    },
    "Cybersecurity / Security Administrator": {
        "esco_uri": "http://data.europa.eu/esco/occupation/e5658e39-e93d-4c3d-bd83-fba01f84faeb",
        "isco_group": "2529",
        "onet_code": "15-1212.00",
        "description": "Cybersecurity administrators protect organizational networks, servers, and data systems from threats, vulnerabilities, and unauthorized access.",
        "essential_skills": [
            "Cybersecurity Fundamentals", "Network Security", "Firewalls", "VPN",
            "Vulnerability Assessment", "Incident Response", "Threat Detection",
            "Identity & Access Management", "Linux Security", "Cryptography"
        ],
        "optional_skills": [
            "SIEM", "Security Log Analysis", "Windows Security",
            "SSL/TLS", "Security Compliance"
        ],
        "skills": [
            "Cybersecurity Fundamentals", "Network Security", "Firewalls", "VPN",
            "Vulnerability Assessment", "Incident Response", "Threat Detection",
            "SIEM", "Security Log Analysis", "Identity & Access Management",
            "Linux Security", "Windows Security", "Cryptography", "SSL/TLS",
            "Security Compliance"
        ]
    },
    "Software QA / Test Engineer": {
        "esco_uri": "http://data.europa.eu/esco/occupation/106f79e4-6264-45f1-9e7a-297435cd684b",
        "isco_group": "2519",
        "onet_code": "15-1253.00",
        "description": "Software QA and test engineers design, automate, and execute testing strategies to ensure software functionality, reliability, and performance.",
        "essential_skills": [
            "Software Testing Fundamentals", "Test Case Design", "Test Planning",
            "Manual Testing", "Functional Testing", "Regression Testing",
            "API Testing", "Test Automation", "Unit Testing", "Bug Tracking / Jira"
        ],
        "optional_skills": [
            "Integration Testing", "Selenium", "Playwright / Cypress",
            "Performance Testing", "Load Testing"
        ],
        "skills": [
            "Software Testing Fundamentals", "Test Case Design", "Test Planning",
            "Manual Testing", "Functional Testing", "Regression Testing",
            "Integration Testing", "API Testing", "Selenium",
            "Playwright / Cypress", "Test Automation", "Unit Testing",
            "Performance Testing", "Load Testing", "Bug Tracking / Jira"
        ]
    },
    "Data Engineer": {
        "esco_uri": "http://data.europa.eu/esco/occupation/2079755f-d809-49e6-8037-4de6180e54c0",
        "isco_group": "2511",
        "onet_code": "15-1243.00",
        "description": "Data engineers build scalable data collection pipelines, transform and clean data streams, and maintain analytical data warehouses.",
        "essential_skills": [
            "Python", "SQL", "Data Modeling", "ETL / ELT", "Apache Spark",
            "Data Pipelines", "Apache Airflow", "Data Warehousing",
            "PostgreSQL / MySQL", "Docker"
        ],
        "optional_skills": [
            "Apache Kafka", "Data Lakes", "NoSQL Databases",
            "Cloud Data Services", "Data Quality"
        ],
        "skills": [
            "Python", "SQL", "Data Modeling", "ETL / ELT", "Apache Spark",
            "Apache Kafka", "Data Pipelines", "Apache Airflow",
            "Data Warehousing", "Data Lakes", "PostgreSQL / MySQL",
            "NoSQL Databases", "Cloud Data Services", "Docker", "Data Quality"
        ]
    },
    "Backend Developer": {
        "esco_uri": "http://data.europa.eu/esco/occupation/f2b15a0e-e65a-438a-affb-29b9d50b77d1",
        "isco_group": "2512",
        "onet_code": "15-1252.00",
        "description": "Backend developers architect server-side logic, database interactions, microservices, and robust APIs powering client-side applications.",
        "essential_skills": [
            "Node.js", "Python / FastAPI", "Java / Spring Boot",
            "REST API Development", "SQL", "PostgreSQL", "Redis / Caching",
            "Authentication", "Authorization", "Docker"
        ],
        "optional_skills": [
            "Express.js / Fastify", "GraphQL", "JWT / OAuth",
            "Microservices", "Backend Performance Optimization"
        ],
        "skills": [
            "Node.js", "Express.js / Fastify", "Java / Spring Boot",
            "Python / FastAPI", "REST API Development", "GraphQL", "SQL",
            "PostgreSQL", "Redis / Caching", "Authentication", "Authorization",
            "JWT / OAuth", "Microservices", "Docker",
            "Backend Performance Optimization"
        ]
    },
    "Machine Learning Engineer": {
        "esco_uri": "http://data.europa.eu/esco/occupation/781a6350-e686-45b9-b075-e4c8d5a05ff7",
        "isco_group": "2512",
        "onet_code": "15-2051.01",
        "description": "Machine learning engineers build, train, optimize, deploy, and monitor production machine learning models and neural networks.",
        "essential_skills": [
            "Python", "NumPy", "Pandas", "Scikit-learn", "PyTorch",
            "Machine Learning Algorithms", "Deep Learning", "Feature Engineering",
            "Model Serving", "Docker"
        ],
        "optional_skills": [
            "TensorFlow", "Model Evaluation", "Hyperparameter Optimization",
            "NLP / Computer Vision", "MLOps"
        ],
        "skills": [
            "Python", "NumPy", "Pandas", "Scikit-learn", "PyTorch",
            "TensorFlow", "Machine Learning Algorithms", "Deep Learning",
            "Feature Engineering", "Model Evaluation",
            "Hyperparameter Optimization", "NLP / Computer Vision",
            "Model Serving", "Docker", "MLOps"
        ]
    },
    "Network & Systems Administrator": {
        "esco_uri": "http://data.europa.eu/esco/occupation/81480b40-a318-47f3-9b2c-56b69ed67d95",
        "isco_group": "2522",
        "onet_code": "15-1244.00",
        "description": "Network and systems administrators configure, support, monitor, and troubleshoot network infrastructure, routers, switches, and server operating systems.",
        "essential_skills": [
            "Linux Administration", "Windows Server Administration", "TCP/IP",
            "DNS", "DHCP", "Routing", "Switching", "Firewalls",
            "Network Troubleshooting", "Active Directory"
        ],
        "optional_skills": [
            "VLAN", "VPN", "Network Monitoring", "PowerShell",
            "Backup & Disaster Recovery"
        ],
        "skills": [
            "Linux Administration", "Windows Server Administration", "TCP/IP",
            "DNS", "DHCP", "Routing", "Switching", "VLAN", "VPN",
            "Firewalls", "Network Monitoring", "Network Troubleshooting",
            "Active Directory", "PowerShell", "Backup & Disaster Recovery"
        ]
    },
    "Solutions / Software Architect": {
        "esco_uri": "http://data.europa.eu/esco/occupation/d0aa0792-4345-474b-9365-686cf4869d2e",
        "isco_group": "2512",
        "onet_code": "15-1252.00",
        "description": "Solutions and software architects design large-scale, distributed system architectures, establishing technical standards, scalability patterns, and security frameworks.",
        "essential_skills": [
            "Software Architecture", "System Design", "Distributed Systems",
            "Microservices Architecture", "API Architecture", "Database Architecture",
            "Cloud Architecture", "Scalability", "High Availability", "Security Architecture"
        ],
        "optional_skills": [
            "REST / GraphQL", "Fault Tolerance", "Caching",
            "Message Queues", "Architecture Design Patterns"
        ],
        "skills": [
            "Software Architecture", "System Design", "Distributed Systems",
            "Microservices Architecture", "API Architecture", "REST / GraphQL",
            "Database Architecture", "Cloud Architecture", "Scalability",
            "High Availability", "Fault Tolerance", "Caching", "Message Queues",
            "Security Architecture", "Architecture Design Patterns"
        ]
    }
}

ROLE_ALIASES = {
    "web developer": "Web Developer",
    "software developer": "Software Developer",
    "data scientist": "Data Scientist",
    "cloud devops engineer": "Cloud / DevOps Engineer",
    "cloud / devops engineer": "Cloud / DevOps Engineer",
    "database administrator": "Database Administrator",
    "ict system analyst": "ICT System Analyst",
    "mobile application developer": "Mobile Application Developer",
    "user interface developer": "UI / Frontend Developer",
    "ui / frontend developer": "UI / Frontend Developer",
    "ict security administrator": "Cybersecurity / Security Administrator",
    "cybersecurity / security administrator": "Cybersecurity / Security Administrator",
    "software qa / test engineer": "Software QA / Test Engineer",
    "data engineer": "Data Engineer",
    "backend developer": "Backend Developer",
    "machine learning engineer": "Machine Learning Engineer",
    "network & systems administrator": "Network & Systems Administrator",
    "solutions / software architect": "Solutions / Software Architect",
}

# Backward compatibility mappings for legacy callers
ONET_IT_MAPPING = {name.lower(): data["onet_code"] for name, data in TAXONOMY_15_ROLES.items()}
ESCO_IT_OCCUPATION_URIS = {name.lower(): data["esco_uri"] for name, data in TAXONOMY_15_ROLES.items()}

# Skill category inference from ESCO skill labels (keyword → category)
SKILL_CATEGORY_MAP = [
    (["python", "java", "javascript", "c++", "c#", "sql", "r ", "php",
      "ruby", "scala", "go ", "kotlin", "swift", "typescript", "html", "css"],
     "Programming"),
    (["machine learning", "deep learning", "neural network", "tensorflow",
      "pytorch", "scikit", "nlp", "natural language", "computer vision",
      "reinforcement learning", "ai ", "artificial intelligence"],
     "Artificial Intelligence"),
    (["database", "sql", "nosql", "mongodb", "postgresql", "mysql",
      "oracle", "sqlite", "redis", "data model"],
     "Database"),
    (["docker", "kubernetes", "devops", "ci/cd", "jenkins", "git",
      "ansible", "terraform", "cloud", "aws", "azure", "gcp",
      "linux", "unix", "shell", "bash", "deployment"],
     "DevOps"),
    (["rest", "api", "microservice", "web service", "http", "json",
      "xml", "graphql", "soap", "backend"],
     "Backend"),
    (["test", "debugging", "debug", "quality assurance", "qa ",
      "unit test", "selenium", "junit"],
     "Testing"),
    (["project management", "agile", "scrum", "kanban", "leadership",
      "communication", "teamwork", "problem solving"],
     "Soft Skills"),
    (["statistics", "mathematics", "linear algebra", "calculus",
      "data analysis", "pandas", "numpy", "visualization"],
     "Data Science"),
    (["security", "cryptography", "firewall", "vulnerability",
      "penetration", "cybersecurity", "ethical hack"],
     "Security"),
    (["software design", "architecture", "design pattern", "uml",
      "object-oriented", "oop", "solid"],
     "Software Engineering"),
]


def infer_skill_category(skill_label: str) -> str:
    lower = skill_label.lower()
    for keywords, category in SKILL_CATEGORY_MAP:
        if any(kw in lower for kw in keywords):
            return category
    return "General"


def get_or_create_skill(name: str, source_uri: str = None, category: str = None) -> Skill:
    """Return existing Skill or create a new one. Normalizes name through SkillNormalizer."""
    from services.skill_normalizer import canonicalize_skill_name
    canon = canonicalize_skill_name(name)
    name = (canon or name).strip()[:140]
    s = Skill.query.filter(db.func.lower(Skill.name) == name.lower()).first()
    if not s:
        cat = category or infer_skill_category(name)
        s = Skill(
            name=name, category=cat,
            source="ESCO" if source_uri else "CANONICAL",
            source_identifier=source_uri
        )
        db.session.add(s)
        db.session.flush()
    return s


# ─────────────────────────────────────────────────────────────────────────────
# ESCO Ingestion
# ─────────────────────────────────────────────────────────────────────────────
def ingest_esco(esco_dir: str) -> dict:
    """
    Ingest IT occupations and their skills from ESCO v1.2.1 CSV files.
    Returns a summary dict of counts.
    """
    esco_path = Path(esco_dir)
    occ_file = esco_path / "occupations_en.csv"
    rel_file = esco_path / "occupationSkillRelations_en.csv"

    if not occ_file.exists() or not rel_file.exists():
        print(f"  [ESCO] WARNING: CSV files not found at {esco_dir}. Skipping ESCO ingestion.")
        return {"roles": 0, "skills": 0, "job_skills": 0}

    print(f"  [ESCO] Loading occupations from {occ_file}...")

    # Build URI → occupation data map for IT roles
    occ_map = {}
    with open(occ_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["conceptUri"] in ESCO_IT_OCCUPATION_URIS.values():
                occ_map[row["conceptUri"]] = {
                    "name": row["preferredLabel"],
                    "isco_group": row.get("iscoGroup", ""),
                    "description": row.get("description", "")[:500],
                }

    # Create JobRole records
    roles_created = 0
    role_id_map = {}  # URI → db row id
    for uri, data in occ_map.items():
        existing = JobRole.query.filter_by(source="ESCO", source_identifier=uri).first()
        if not existing:
            role = JobRole(
                name=data["name"],
                source="ESCO",
                source_identifier=uri,
                description=data.get("description", ""),
                isco_group=data.get("isco_group", "")
            )
            db.session.add(role)
            db.session.flush()
            role_id_map[uri] = role.id
            roles_created += 1
        else:
            role_id_map[uri] = existing.id
    print(f"  [ESCO] {roles_created} new JobRole records (IT occupations).")

    # Ingest occupation-skill relations
    print(f"  [ESCO] Loading skill relations from {rel_file}...")
    skills_created = 0
    job_skills_created = 0

    with open(rel_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            occ_uri = row["occupationUri"]
            if occ_uri not in role_id_map:
                continue

            skill_label = row["skillLabel"].strip()
            skill_uri = row["skillUri"]
            relation_type = row["relationType"]   # essential | optional

            skill = get_or_create_skill(skill_label, skill_uri)
            if skill.id not in [s.id for s in [skill]]:
                skills_created += 1

            # required_level and importance: essential = 75–80, optional = 55–65
            required_level = 78.0 if relation_type == "essential" else 60.0
            importance = 1.0 if relation_type == "essential" else 0.7

            existing_js = JobSkill.query.filter_by(
                job_role_id=role_id_map[occ_uri], skill_id=skill.id
            ).first()
            if not existing_js:
                db.session.add(JobSkill(
                    job_role_id=role_id_map[occ_uri],
                    skill_id=skill.id,
                    required_level=required_level,
                    importance=importance,
                    relation_type=relation_type,
                    source="ESCO"
                ))
                job_skills_created += 1

    db.session.commit()
    # Count new skills (approximate after flush)
    skills_created = Skill.query.filter_by(source="ESCO").count()
    print(f"  [ESCO] {skills_created} ESCO skills total, {job_skills_created} new JobSkill records.")
    return {"roles": roles_created, "skills": skills_created, "job_skills": job_skills_created}


# ─────────────────────────────────────────────────────────────────────────────
# O*NET Ingestion
# ─────────────────────────────────────────────────────────────────────────────
def ingest_onet(
    knowledge_path: str,
    activities_path: str,
    occupations_path: str,
    im_threshold_knowledge: float = 2.5,
    im_threshold_activities: float = 3.0,
) -> dict:
    """
    Ingest O*NET Knowledge and Work Activity competencies for the 6 IT roles.

    Normalization formulas (PRD Section: Dual Taxonomy):
        importance  = clamp(IM / 5.0, 0.1, 1.0)
        req_level   = round(LV / 7.0 * 5.0), clamped to [1, 5]

    Each competency is stored as a Skill with:
        category = "O*NET Knowledge"  or  "O*NET Work Activity"
        source   = "O*NET"

    Idempotent: skips existing JobSkill rows.
    """
    try:
        import openpyxl
    except ImportError:
        print("  [O*NET] openpyxl not installed. Skipping O*NET ingestion.")
        return {"skills": 0, "job_skills": 0, "roles_updated": 0}

    for path in (knowledge_path, activities_path, occupations_path):
        if not Path(path).exists():
            print(f"  [O*NET] WARNING: {path} not found. Skipping O*NET ingestion.")
            return {"skills": 0, "job_skills": 0, "roles_updated": 0}

    # ── Step 1: Load O*NET occupation data to patch JobRole.onet_code ──────────
    print(f"  [O*NET] Loading occupation data from {occupations_path}...")
    onet_occupation_map: dict[str, dict] = {}   # onet_code → {title, description}
    wb_occ = openpyxl.load_workbook(occupations_path, read_only=True, data_only=True)
    ws_occ = wb_occ.active
    occ_rows = list(ws_occ.iter_rows(values_only=True))
    occ_header = [str(h).strip() for h in occ_rows[0]]
    for raw in occ_rows[1:]:
        row = dict(zip(occ_header, raw))
        code = str(row.get("O*NET-SOC Code") or "").strip()
        if code:
            onet_occupation_map[code] = {
                "title":       str(row.get("Title") or "").strip(),
                "description": str(row.get("Description") or "").strip()[:500],
            }
    wb_occ.close()

    # ── Step 2: Patch JobRole rows with their O*NET code ──────────────────────
    roles_updated = 0
    # Build canonical name → db JobRole mapping
    role_db_map: dict[str, "JobRole"] = {}  # canonical lower name → JobRole obj
    for canonical_name, onet_code in ONET_IT_MAPPING.items():
        # Match against ESCO-sourced roles (case-insensitive substring)
        roles = JobRole.query.filter(JobRole.source == "ESCO").all()
        for r in roles:
            if canonical_name in r.name.lower():
                if r.onet_code != onet_code:
                    r.onet_code = onet_code
                    roles_updated += 1
                role_db_map[canonical_name] = r
                break
    db.session.flush()
    print(f"  [O*NET] Patched {roles_updated} JobRole rows with O*NET-SOC codes.")

    # ── Step 3: Helper to read and process one O*NET XLSX file ────────────────
    def _process_onet_file(
        xlsx_path: str,
        skill_category: str,
        im_threshold: float,
    ) -> tuple[int, int]:
        """
        Read the O*NET xlsx, filter to IT SOC codes above IM threshold,
        normalise scores, and upsert Skill + JobSkill records.
        Returns (skills_created, job_skills_created).
        """
        wb = openpyxl.load_workbook(xlsx_path, read_only=True, data_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        header = [str(h).strip() for h in rows[0]]
        wb.close()

        # Build: onet_code → element_name → {IM, LV}
        # We need BOTH IM and LV rows for the same element to compute req_level.
        ElementData = dict  # {"IM": float, "LV": float}
        per_occ: dict[str, dict[str, ElementData]] = {}

        target_codes = set(ONET_IT_MAPPING.values())
        for raw in rows[1:]:
            row = dict(zip(header, raw))
            code = str(row.get("O*NET-SOC Code") or "").strip()
            if code not in target_codes:
                continue
            element_name = str(row.get("Element Name") or "").strip()
            scale_id = str(row.get("Scale ID") or "").strip()
            suppress = str(row.get("Recommend Suppress") or "N").strip()
            if suppress == "Y" or not element_name:
                continue
            try:
                data_value = float(row.get("Data Value") or 0)
            except (TypeError, ValueError):
                continue

            per_occ.setdefault(code, {}).setdefault(element_name, {})
            per_occ[code][element_name][scale_id] = data_value

        skills_created_count = 0
        job_skills_created_count = 0

        # Build inverse map: onet_code → canonical role name
        code_to_role: dict[str, "JobRole"] = {}
        for canonical_name, role_obj in role_db_map.items():
            if role_obj.onet_code:
                code_to_role[role_obj.onet_code] = role_obj
            # Also match secondary code for DevOps
            for onet_code in ("15-1241.00", "15-1244.00"):
                if canonical_name == "cloud devops engineer":
                    code_to_role[onet_code] = role_obj

        for onet_code, elements in per_occ.items():
            role_obj = code_to_role.get(onet_code)
            if not role_obj:
                continue

            for element_name, scales in elements.items():
                im_value = scales.get("IM", 0.0)
                lv_value = scales.get("LV", 0.0)

                if im_value < im_threshold:
                    continue  # Below importance threshold — skip

                # Normalization formulas from PRD
                importance = min(1.0, max(0.1, im_value / 5.0))
                req_level_raw = round((lv_value / 7.0) * 5.0) if lv_value > 0 else 3
                req_level = float(max(1, min(5, req_level_raw)))
                # Scale req_level from [1,5] to [0,100] for our proficiency system
                required_level_100 = req_level * 20.0  # 1→20, 2→40, 3→60, 4→80, 5→100

                # Upsert skill
                skill_name = element_name[:140]
                sk = Skill.query.filter(
                    db.func.lower(Skill.name) == skill_name.lower()
                ).first()
                if not sk:
                    sk = Skill(
                        name=skill_name,
                        category=skill_category,
                        source="O*NET",
                        source_identifier=f"onet:{onet_code}:{element_name[:50]}",
                    )
                    db.session.add(sk)
                    db.session.flush()
                    skills_created_count += 1
                elif sk.source == "CANONICAL" or sk.source == "ESCO":
                    pass  # Don't overwrite ESCO/canonical skills

                # Upsert job_skill
                existing = JobSkill.query.filter_by(
                    job_role_id=role_obj.id, skill_id=sk.id
                ).first()
                if not existing:
                    db.session.add(JobSkill(
                        job_role_id=role_obj.id,
                        skill_id=sk.id,
                        required_level=required_level_100,
                        importance=importance,
                        relation_type="essential",
                        source="O*NET",
                    ))
                    job_skills_created_count += 1

        db.session.commit()
        return skills_created_count, job_skills_created_count

    # ── Step 4: Process both O*NET files ──────────────────────────────────────
    print(f"  [O*NET] Processing Knowledge file (IM >= {im_threshold_knowledge})...")
    k_skills, k_js = _process_onet_file(
        knowledge_path, "O*NET Knowledge", im_threshold_knowledge
    )
    print(f"  [O*NET] Knowledge: {k_skills} new skills, {k_js} new JobSkill records.")

    print(f"  [O*NET] Processing Work Activities file (IM >= {im_threshold_activities})...")
    w_skills, w_js = _process_onet_file(
        activities_path, "O*NET Work Activity", im_threshold_activities
    )
    print(f"  [O*NET] Work Activities: {w_skills} new skills, {w_js} new JobSkill records.")

    total_skills = k_skills + w_skills
    total_js = k_js + w_js
    print(f"  [O*NET] Total: {total_skills} new competency skills, "
          f"{total_js} new JobSkill records, {roles_updated} roles updated.")
    return {"skills": total_skills, "job_skills": total_js, "roles_updated": roles_updated}


# ─────────────────────────────────────────────────────────────────────────────
# Coursera Dataset Ingestion
# ─────────────────────────────────────────────────────────────────────────────

# IT-relevant Coursera skills to filter and map to canonical skills
IT_SKILL_KEYWORDS = {
    "python", "java", "javascript", "sql", "machine learning", "deep learning",
    "data science", "web development", "docker", "kubernetes", "devops",
    "cloud", "aws", "azure", "git", "database", "nosql", "mongodb",
    "rest", "api", "html", "css", "react", "node", "angular", "flask",
    "django", "spring", "testing", "agile", "scrum", "linux", "security",
    "nlp", "tensorflow", "pytorch", "pandas", "numpy", "r programming",
    "statistics", "data analysis", "big data", "spark", "hadoop",
    "c++", "c#", "kotlin", "swift", "typescript", "ruby", "scala",
    "software design", "object-oriented", "algorithms", "data structures",
    "cryptography", "cybersecurity", "ethical hacking",
}


def _coursera_skill_to_canonical(raw_skill: str) -> str | None:
    """Normalize a Coursera skill tag to a canonical-ish label."""
    s = raw_skill.strip().lower()
    if not s or len(s) > 50:
        return None
    # Filter to IT skills
    if not any(kw in s for kw in IT_SKILL_KEYWORDS):
        return None
    # Normalize common variations
    norm = {
        "python programming": "Python", "python 3": "Python",
        "java programming": "Java", "javascript basics": "JavaScript",
        "sql programming": "SQL", "mysql": "MySQL",
        "machine learning": "Machine Learning", "ml": "Machine Learning",
        "deep learning": "Deep Learning", "neural networks": "Deep Learning",
        "web development": "Web Development", "web design": "Web Development",
        "docker": "Docker", "kubernetes": "Kubernetes",
        "cloud computing": "Cloud Computing", "aws": "AWS",
        "git": "Git", "github": "Git",
        "rest api": "REST API", "restful api": "REST API",
        "software testing": "Software Testing", "unit testing": "Software Testing",
        "natural language processing": "NLP", "nlp": "NLP",
        "data analysis": "Data Analysis",
        "data visualization": "Data Visualization",
        "software design": "Software Design",
        "algorithms": "Algorithms & Data Structures",
        "data structures": "Algorithms & Data Structures",
    }
    return norm.get(s, raw_skill.strip()[:50].title())


def ingest_coursera(coursera_source: str) -> dict:
    """
    Ingest Coursera courses from Coursera.csv (or Coursera.zip / archive.zip).
    Only ingests IT-relevant courses (based on Skills column keywords).
    """
    source_path = Path(coursera_source)
    if not source_path.exists():
        # Check alternative csv / zip extensions
        alt_csv = source_path.with_name("Coursera.csv")
        alt_zip = source_path.with_name("Coursera.zip")
        if alt_csv.exists():
            source_path = alt_csv
        elif alt_zip.exists():
            source_path = alt_zip
        else:
            print(f"  [Coursera] WARNING: {coursera_source} not found. Skipping.")
            return {"courses": 0, "course_skills": 0}

    print(f"  [Coursera] Loading courses from {source_path}...")

    courses_created = 0
    course_skills_created = 0

    def _process_reader(reader):
        nonlocal courses_created, course_skills_created
        for row in reader:
            raw_skills_str = row.get("Skills", "")
            if not raw_skills_str:
                continue

            # Parse skills field (semicolon, comma, or double-space separated)
            raw_skills = [
                s.strip() for s in re.split(r"[;,]|\s{2,}", raw_skills_str) if s.strip()
            ]
            canonical_skills = [
                _coursera_skill_to_canonical(s) for s in raw_skills
            ]
            canonical_skills = [s for s in canonical_skills if s]

            if not canonical_skills:
                continue  # Skip non-IT courses

            title = (row.get("Course Name") or "").strip()
            provider = (row.get("University") or "Coursera").strip()
            url = (row.get("Course URL") or "").strip()
            description = (row.get("Course Description") or "").strip()[:600]
            difficulty = (row.get("Difficulty Level") or "").strip()
            try:
                rating = float(row.get("Course Rating") or 0)
            except (ValueError, TypeError):
                rating = 0.0

            if not title:
                continue

            # Upsert course (avoid duplicates by title+provider)
            course = Course.query.filter_by(title=title, provider=provider).first()
            if not course:
                course = Course(
                    title=title, provider=provider, url=url,
                    description=description, difficulty_level=difficulty,
                    rating=rating, source="Coursera"
                )
                db.session.add(course)
                db.session.flush()
                courses_created += 1

            # Map canonical skills to CourseSkill
            for skill_name in canonical_skills:
                skill = get_or_create_skill(skill_name)
                existing = CourseSkill.query.filter_by(
                    course_id=course.id, skill_id=skill.id
                ).first()
                if not existing:
                    db.session.add(CourseSkill(
                        course_id=course.id, skill_id=skill.id, relevance=0.9
                    ))
                    course_skills_created += 1

    if source_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(source_path) as z:
            csv_names = [n for n in z.namelist() if n.endswith(".csv")]
            target = "Coursera.csv" if "Coursera.csv" in csv_names else (csv_names[0] if csv_names else None)
            if not target:
                print(f"  [Coursera] No CSV found inside {source_path}.")
                return {"courses": 0, "course_skills": 0}
            with z.open(target) as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8", errors="replace"))
                _process_reader(reader)
    else:
        with open(source_path, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            _process_reader(reader)

    db.session.commit()
    print(f"  [Coursera] {courses_created} new courses, {course_skills_created} new CourseSkill records.")
    return {"courses": courses_created, "course_skills": course_skills_created}


# ─────────────────────────────────────────────────────────────────────────────
# Student Dataset Ingestion
# ─────────────────────────────────────────────────────────────────────────────
def ingest_students(student_xlsx: str, max_students: int = 20) -> dict:
    """
    Ingest sample student profiles and self-reported skills from
    Final_Updated_DMA_DATASET_Indian_Names (1).xlsx.
    """
    if not Path(student_xlsx).exists():
        print(f"  [Students] WARNING: {student_xlsx} not found. Skipping.")
        return {"students": 0, "student_skills": 0}

    print(f"  [Students] Loading student profiles from {student_xlsx}...")

    try:
        import openpyxl
    except ImportError:
        print("  [Students] openpyxl not installed. Skipping student ingestion.")
        return {"students": 0, "student_skills": 0}

    wb = openpyxl.load_workbook(student_xlsx, read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    header = [str(h).strip() if h else "" for h in rows[0]]

    students_created = 0
    student_skills_created = 0

    for raw in rows[1: max_students + 1]:
        row = dict(zip(header, raw))
        name = str(row.get("name") or "").strip()
        email = str(row.get("email_id") or "").strip()
        if not name or not email:
            continue

        # Skip if email already exists
        if Student.query.filter_by(email=email).first():
            continue

        year_str = str(row.get("year") or "").strip()
        year_map = {"1st Year": 1, "2nd Year": 2, "3rd Year": 3, "4th Year": 4}
        year = year_map.get(year_str, 1)
        course = str(row.get("current_course") or "MCA").strip()
        aspiration = str(row.get("job_role_aspiration") or "").strip()

        s = Student(
            name=name, email=email,
            course=course, year=year, target_career=aspiration
        )
        db.session.add(s)
        db.session.flush()
        students_created += 1

        # Parse technical_skills + rating
        skills_raw = str(row.get("technical_skills") or "").strip()
        rating_raw = str(row.get("rating") or "3").strip()
        try:
            rating_value = float(rating_raw) * 20  # Convert 1-5 scale to 0-100
        except (ValueError, TypeError):
            rating_value = 60.0

        if skills_raw:
            for sk_name in re.split(r"[;,]", skills_raw):
                sk_name = sk_name.strip()
                if not sk_name:
                    continue
                skill = get_or_create_skill(sk_name)
                existing = StudentSkill.query.filter_by(
                    student_id=s.id, skill_id=skill.id
                ).first()
                if not existing:
                    db.session.add(StudentSkill(
                        student_id=s.id, skill_id=skill.id,
                        proficiency=min(rating_value, 100),
                        evidence_type="self_reported",
                        confidence=0.9
                    ))
                    student_skills_created += 1

        # Parse programming_languages
        langs_raw = str(row.get("programming_languages") or "").strip()
        if langs_raw:
            for lang in re.split(r"[;,]", langs_raw):
                lang = lang.strip()
                if not lang:
                    continue
                skill = get_or_create_skill(lang, category="Programming")
                existing = StudentSkill.query.filter_by(
                    student_id=s.id, skill_id=skill.id
                ).first()
                if not existing:
                    db.session.add(StudentSkill(
                        student_id=s.id, skill_id=skill.id,
                        proficiency=min(rating_value, 100),
                        evidence_type="self_reported",
                        confidence=0.9
                    ))
                    student_skills_created += 1

    db.session.commit()
    wb.close()
    print(f"  [Students] {students_created} new students, {student_skills_created} new StudentSkill records.")
    return {"students": students_created, "student_skills": student_skills_created}


# ─────────────────────────────────────────────────────────────────────────────
# Master ingestion function
# ─────────────────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
# Definitive 15 Roles Synchronization
# ─────────────────────────────────────────────────────────────────────────────
def sync_15_roles_and_skills() -> dict:
    """
    Calibrate and synchronize the database to the definitive 15 IT Roles × 15 Core Skills taxonomy.
    Grounded in official ESCO v1.2.1 concept URIs, ISCO-08 groups, and O*NET-SOC codes.
    Guarantees that each of the 15 roles has exactly 15 high-priority skills.
    """
    from models import SkillGap

    print("\n=== Synchronizing 15 Roles × 15 Core Skills ===")
    roles_synced = 0
    skills_created_or_mapped = 0
    total_job_skills = 0

    # Build lookup of existing roles by normalized name
    existing_roles = {r.name.lower().strip(): r for r in JobRole.query.all()}

    for role_name, role_data in TAXONOMY_15_ROLES.items():
        # Match existing role by exact title or alias
        role = existing_roles.get(role_name.lower().strip())
        if not role:
            # Check aliases
            for alias_key, canon_name in ROLE_ALIASES.items():
                if canon_name == role_name and alias_key in existing_roles:
                    role = existing_roles[alias_key]
                    break

        if not role:
            role = JobRole(
                name=role_name,
                source="ESCO",
                source_identifier=role_data["esco_uri"],
                description=role_data["description"],
                isco_group=role_data["isco_group"],
                onet_code=role_data["onet_code"],
            )
            db.session.add(role)
            db.session.flush()
        else:
            # Update canonical attributes
            role.name = role_name
            role.source = "ESCO"
            role.source_identifier = role_data["esco_uri"]
            role.description = role_data["description"]
            role.isco_group = role_data["isco_group"]
            role.onet_code = role_data["onet_code"]
            db.session.flush()

        roles_synced += 1

        # Map the 15 skills for this role (10 Essential + 5 Optional)
        target_skill_ids = []
        essential_list = role_data.get("essential_skills", role_data["skills"][:10])
        optional_list = role_data.get("optional_skills", role_data["skills"][10:])

        for skill_name in essential_list:
            skill = get_or_create_skill(skill_name)
            target_skill_ids.append(skill.id)
            skills_created_or_mapped += 1

            js = JobSkill.query.filter_by(job_role_id=role.id, skill_id=skill.id).first()
            if not js:
                js = JobSkill(
                    job_role_id=role.id,
                    skill_id=skill.id,
                    required_level=75.0,
                    importance=1.0,
                    relation_type="essential",
                    source="ESCO",
                )
                db.session.add(js)
            else:
                js.required_level = 75.0
                js.importance = 1.0
                js.relation_type = "essential"
                js.source = "ESCO"

        for skill_name in optional_list:
            skill = get_or_create_skill(skill_name)
            target_skill_ids.append(skill.id)
            skills_created_or_mapped += 1

            js = JobSkill.query.filter_by(job_role_id=role.id, skill_id=skill.id).first()
            if not js:
                js = JobSkill(
                    job_role_id=role.id,
                    skill_id=skill.id,
                    required_level=60.0,
                    importance=0.5,
                    relation_type="optional",
                    source="ESCO",
                )
                db.session.add(js)
            else:
                js.required_level = 60.0
                js.importance = 0.5
                js.relation_type = "optional"
                js.source = "ESCO"

        # Remove any extraneous job skills outside the 15 curated skills
        old_js = JobSkill.query.filter(
            JobSkill.job_role_id == role.id,
            ~JobSkill.skill_id.in_(target_skill_ids)
        ).all()
        old_skill_ids = [o.skill_id for o in old_js]
        if old_skill_ids:
            SkillGap.query.filter(
                SkillGap.job_role_id == role.id,
                SkillGap.skill_id.in_(old_skill_ids)
            ).delete(synchronize_session=False)

            JobSkill.query.filter(
                JobSkill.job_role_id == role.id,
                ~JobSkill.skill_id.in_(target_skill_ids)
            ).delete(synchronize_session=False)

        total_job_skills += len(target_skill_ids)

    db.session.commit()
    print(f"  Synced {roles_synced} roles.")
    print(f"  Total active JobSkill mappings: {total_job_skills} (15 per role).")
    return {
        "roles": roles_synced,
        "skills_per_role": 15,
        "total_job_skills": total_job_skills
    }


def run_ingestion() -> dict:
    """
    Run the full ingestion pipeline in order:
    1. Synchronize 15 Roles x 15 Core Skills (ESCO + O*NET)
    2. Coursera courses
    3. Student profiles
    """
    cfg = current_app.config
    print("\n=== Starting Data Ingestion Pipeline ===")

    summary = {}

    print("\n[1/3] 15 Roles × 15 Core Skills Synchronization")
    summary["roles_and_skills"] = sync_15_roles_and_skills()

    print("\n[3/4] Coursera Dataset Ingestion")
    coursera_source = cfg.get("COURSERA_CSV") or cfg.get("COURSERA_ZIP")
    summary["coursera"] = ingest_coursera(coursera_source)

    print("\n[4/4] Student Dataset Ingestion")
    summary["students"] = ingest_students(cfg["STUDENT_DATASET_XLSX"])

    print("\n=== Ingestion Complete ===")
    print(f"  ESCO:     {summary['esco']['roles']} IT roles, "
          f"{summary['esco']['job_skills']} job-skill mappings")
    print(f"  O*NET:    {summary['onet']['skills']} competency skills, "
          f"{summary['onet']['job_skills']} job-skill mappings, "
          f"{summary['onet']['roles_updated']} roles updated with SOC code")
    print(f"  Coursera: {summary['coursera']['courses']} courses, "
          f"{summary['coursera']['course_skills']} course-skill mappings")
    print(f"  Students: {summary['students']['students']} students, "
          f"{summary['students']['student_skills']} student skills")

    return summary
