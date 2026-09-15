"""
seed.py — Populates demo data (skills, job roles, job-skill mappings, courses) into the DB.

Run via: flask --app app seed

This ensures the application is fully functional immediately after first setup,
even without running the full `flask ingest-data` pipeline.

For production data (1,612 Coursera courses + ESCO taxonomy + 22 student profiles),
run: flask --app app ingest-data
"""
from extensions import db
from models import Course, CourseSkill, JobRole, JobSkill, Skill


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _get_or_create_skill(name: str, category: str) -> "Skill":
    s = Skill.query.filter_by(name=name).first()
    if not s:
        s = Skill(name=name, category=category, source="CANONICAL")
        db.session.add(s)
        db.session.flush()
    return s


def _get_or_create_role(name: str, source_id: str, description: str = "") -> "JobRole":
    r = JobRole.query.filter_by(name=name, source="DEMO").first()
    if not r:
        r = JobRole(name=name, source="DEMO",
                    source_identifier=source_id, description=description)
        db.session.add(r)
        db.session.flush()
    return r


def _map_role_skill(role: "JobRole", skill: "Skill",
                    required_level: float, importance: float,
                    relation_type: str = "essential") -> None:
    from models import JobSkill
    exists = JobSkill.query.filter_by(
        job_role_id=role.id, skill_id=skill.id
    ).first()
    if not exists:
        db.session.add(JobSkill(
            job_role_id=role.id, skill_id=skill.id,
            required_level=required_level, importance=importance,
            relation_type=relation_type, source="DEMO"
        ))


def _get_or_create_course(title: str, provider: str, description: str,
                           url: str, difficulty: str, rating: float) -> "Course":
    c = Course.query.filter_by(title=title, provider=provider).first()
    if not c:
        c = Course(title=title, provider=provider, description=description,
                   url=url, difficulty_level=difficulty, rating=rating,
                   source="Demo")
        db.session.add(c)
        db.session.flush()
    return c


def _map_course_skill(course: "Course", skill: "Skill", relevance: float = 1.0) -> None:
    exists = CourseSkill.query.filter_by(
        course_id=course.id, skill_id=skill.id
    ).first()
    if not exists:
        db.session.add(CourseSkill(
            course_id=course.id, skill_id=skill.id, relevance=relevance
        ))


# ─────────────────────────────────────────────────────────────────────────────
# Core Skill Catalogue
# ─────────────────────────────────────────────────────────────────────────────
SKILL_DEFS = {
    # Programming
    "Python":              "Programming",
    "Java":                "Programming",
    "JavaScript":          "Programming",
    "TypeScript":          "Programming",
    "C++":                 "Programming",
    "C#":                  "Programming",
    "Go":                  "Programming",
    # Database
    "SQL":                 "Database",
    "MySQL":               "Database",
    "PostgreSQL":          "Database",
    "MongoDB":             "Database",
    "Redis":               "Database",
    # DevOps / Cloud
    "Docker":              "DevOps",
    "Kubernetes":          "DevOps",
    "Git":                 "DevOps",
    "CI/CD":               "DevOps",
    "Linux":               "DevOps",
    "AWS":                 "DevOps",
    "Azure":               "DevOps",
    "GCP":                 "DevOps",
    # Backend / API
    "REST API":            "Backend",
    "Flask":               "Backend",
    "Django":              "Backend",
    "Spring Boot":         "Backend",
    "Microservices":       "Backend",
    # Frontend
    "HTML":                "Frontend",
    "CSS":                 "Frontend",
    "React":               "Frontend",
    "Angular":             "Frontend",
    "Vue.js":              "Frontend",
    # Data Science / AI
    "Machine Learning":    "Artificial Intelligence",
    "Deep Learning":       "Artificial Intelligence",
    "TensorFlow":          "Artificial Intelligence",
    "PyTorch":             "Artificial Intelligence",
    "NLP":                 "Artificial Intelligence",
    "Data Analysis":       "Data Science",
    "Pandas":              "Data Science",
    "NumPy":               "Data Science",
    "Statistics":          "Data Science",
    "Data Visualization":  "Data Science",
    # Testing / SE
    "Software Testing":    "Testing",
    "Pytest":              "Testing",
    "Software Design":     "Software Engineering",
    "Algorithms & Data Structures": "Software Engineering",
    "Design Patterns":     "Software Engineering",
    "System Design":       "Software Engineering",
    # Security
    "Cybersecurity":       "Security",
    "Cryptography":        "Security",
}


# ─────────────────────────────────────────────────────────────────────────────
# Demo Job Roles + Skill Requirements
# ─────────────────────────────────────────────────────────────────────────────
# Format: (skill_name, required_level, importance, relation_type)
ROLE_REQUIREMENTS = {
    "Software Developer": {
        "desc": "Designs, develops, and maintains software applications.",
        "skills": [
            ("Python",               80, 1.0, "essential"),
            ("Java",                 75, 0.9, "essential"),
            ("SQL",                  70, 0.9, "essential"),
            ("REST API",             75, 1.0, "essential"),
            ("Git",                  70, 0.9, "essential"),
            ("Software Testing",     65, 0.8, "essential"),
            ("Software Design",      70, 0.85, "essential"),
            ("Algorithms & Data Structures", 75, 1.0, "essential"),
            ("Docker",               55, 0.7, "optional"),
            ("JavaScript",           60, 0.7, "optional"),
        ],
    },
    "Data Scientist": {
        "desc": "Analyzes large datasets to extract insights and build ML models.",
        "skills": [
            ("Python",               85, 1.0, "essential"),
            ("Machine Learning",     80, 1.0, "essential"),
            ("Statistics",           80, 1.0, "essential"),
            ("Data Analysis",        85, 1.0, "essential"),
            ("Pandas",               80, 0.95, "essential"),
            ("NumPy",                75, 0.9, "essential"),
            ("SQL",                  70, 0.85, "essential"),
            ("Data Visualization",   70, 0.85, "essential"),
            ("Deep Learning",        70, 0.8, "optional"),
            ("TensorFlow",           65, 0.75, "optional"),
        ],
    },
    "Web Developer": {
        "desc": "Builds and maintains web applications (front-end and back-end).",
        "skills": [
            ("HTML",                 80, 1.0, "essential"),
            ("CSS",                  75, 1.0, "essential"),
            ("JavaScript",           85, 1.0, "essential"),
            ("React",                75, 0.9, "essential"),
            ("REST API",             70, 0.9, "essential"),
            ("SQL",                  65, 0.8, "essential"),
            ("Git",                  70, 0.85, "essential"),
            ("Software Testing",     60, 0.7, "optional"),
            ("TypeScript",           65, 0.75, "optional"),
            ("Node.js / Flask",      60, 0.7, "optional"),
        ],
    },
    "Database Administrator": {
        "desc": "Manages and maintains database systems for reliability and performance.",
        "skills": [
            ("SQL",                  90, 1.0, "essential"),
            ("MySQL",                85, 0.95, "essential"),
            ("PostgreSQL",           80, 0.95, "essential"),
            ("MongoDB",              70, 0.8, "essential"),
            ("Redis",                65, 0.75, "essential"),
            ("Linux",                70, 0.85, "essential"),
            ("Python",               65, 0.8, "optional"),
            ("Software Design",      60, 0.7, "optional"),
            ("Cybersecurity",        60, 0.75, "optional"),
        ],
    },
    "DevOps Engineer": {
        "desc": "Automates software delivery pipelines and manages cloud infrastructure.",
        "skills": [
            ("Docker",               85, 1.0, "essential"),
            ("Kubernetes",           80, 1.0, "essential"),
            ("CI/CD",                85, 1.0, "essential"),
            ("Linux",                80, 0.95, "essential"),
            ("AWS",                  75, 0.9, "essential"),
            ("Git",                  80, 0.95, "essential"),
            ("Python",               65, 0.8, "essential"),
            ("Microservices",        70, 0.85, "optional"),
            ("Azure",                60, 0.7, "optional"),
            ("GCP",                  60, 0.7, "optional"),
        ],
    },
    "ML Engineer": {
        "desc": "Builds and deploys production-grade machine learning systems.",
        "skills": [
            ("Python",               85, 1.0, "essential"),
            ("Machine Learning",     85, 1.0, "essential"),
            ("Deep Learning",        80, 0.95, "essential"),
            ("TensorFlow",           75, 0.9, "essential"),
            ("PyTorch",              75, 0.9, "essential"),
            ("NLP",                  70, 0.85, "essential"),
            ("Docker",               70, 0.85, "essential"),
            ("SQL",                  65, 0.8, "optional"),
            ("AWS",                  65, 0.8, "optional"),
            ("Statistics",           75, 0.9, "essential"),
        ],
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Demo Courses
# ─────────────────────────────────────────────────────────────────────────────
DEMO_COURSES = [
    # Python
    ("Python for Everybody",       "Coursera",    "Learn Python from scratch with real projects.",
     "https://www.coursera.org/specializations/python",    "Beginner",    4.8, "Python"),
    ("Python Data Structures",     "Coursera",    "Understand Python's built-in data structures.",
     "https://www.coursera.org/learn/python-data",         "Beginner",    4.7, "Python"),
    ("Advanced Python Programming","Udemy",       "OOP, decorators, async, and design patterns.",
     "https://www.udemy.com/course/advanced-python/",      "Advanced",    4.6, "Python"),
    # Java
    ("Java Programming Masterclass","Udemy",      "Complete Java course from beginner to pro.",
     "https://www.udemy.com/course/java-the-complete-java-developer-course/","Intermediate",4.6,"Java"),
    # JavaScript
    ("The Complete JavaScript Course","Udemy",    "Modern JavaScript, ES6+, OOP, async.",
     "https://www.udemy.com/course/the-complete-javascript-course/","Beginner",4.7,"JavaScript"),
    # SQL / Database
    ("SQL for Data Science",       "Coursera",    "SQL queries for data analysis.",
     "https://www.coursera.org/learn/sql-for-data-science","Beginner",    4.6, "SQL"),
    ("Complete SQL Bootcamp",      "Udemy",       "PostgreSQL hands-on bootcamp.",
     "https://www.udemy.com/course/the-complete-sql-bootcamp/","Beginner",4.7,"PostgreSQL"),
    ("MongoDB Basics",             "MongoDB University","NoSQL fundamentals and document modelling.",
     "https://university.mongodb.com/courses/M001",        "Beginner",    4.5, "MongoDB"),
    # ML / DS
    ("Machine Learning Specialization","Coursera","Andrew Ng's classic ML course.",
     "https://www.coursera.org/specializations/machine-learning-introduction","Intermediate",4.9,"Machine Learning"),
    ("Deep Learning Specialization","Coursera",   "CNNs, RNNs, Transformers by deeplearning.ai.",
     "https://www.coursera.org/specializations/deep-learning","Advanced",  4.9, "Deep Learning"),
    ("Applied Data Science with Python","Coursera","Pandas, matplotlib, scikit-learn.",
     "https://www.coursera.org/specializations/data-science-python","Intermediate",4.6,"Data Analysis"),
    ("Statistics with Python",     "Coursera",    "Inferential statistics, hypothesis testing.",
     "https://www.coursera.org/specializations/statistics-with-python","Intermediate",4.5,"Statistics"),
    # DevOps / Cloud
    ("Docker & Kubernetes Bootcamp","Udemy",      "Container orchestration in practice.",
     "https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/","Intermediate",4.7,"Docker"),
    ("AWS Certified Solutions Architect","Coursera","AWS architecture fundamentals.",
     "https://www.coursera.org/learn/aws-certified-solutions-architect-associate","Intermediate",4.7,"AWS"),
    ("DevOps Foundations",         "LinkedIn Learning","CI/CD, automation, agile devops.",
     "https://www.linkedin.com/learning/devops-foundations","Beginner",   4.5, "CI/CD"),
    ("Linux Command Line Basics",  "Udemy",       "Shell scripting and Linux fundamentals.",
     "https://www.udemy.com/course/linux-command-line-volume1/","Beginner",4.6,"Linux"),
    # Web Dev
    ("The Web Developer Bootcamp", "Udemy",       "HTML, CSS, JavaScript, Node.js full stack.",
     "https://www.udemy.com/course/the-web-developer-bootcamp/","Beginner",4.7,"HTML"),
    ("React — The Complete Guide", "Udemy",       "Hooks, Redux, React Router.",
     "https://www.udemy.com/course/react-the-complete-guide-incl-redux/","Intermediate",4.7,"React"),
    # Backend
    ("REST APIs with Flask and Python","Udemy",   "Build production REST APIs.",
     "https://www.udemy.com/course/rest-api-flask-and-python/","Intermediate",4.6,"REST API"),
    # Testing
    ("Software Testing & Automation","Coursera",  "Unit, integration, and end-to-end testing.",
     "https://www.coursera.org/specializations/software-testing-automation","Intermediate",4.5,"Software Testing"),
    # System Design / SE
    ("System Design Interview",    "educative.io","Scalable system design patterns.",
     "https://www.educative.io/courses/grokking-the-system-design-interview","Advanced",  4.8, "System Design"),
    ("Algorithms Specialization",  "Coursera",    "Sorting, graphs, dynamic programming.",
     "https://www.coursera.org/specializations/algorithms","Intermediate",4.8,"Algorithms & Data Structures"),
    # Security
    ("Cybersecurity Fundamentals", "Coursera",    "Network security and cryptography basics.",
     "https://www.coursera.org/specializations/intro-cyber-security","Beginner",4.5,"Cybersecurity"),
    # NLP
    ("Natural Language Processing","Coursera",    "Text classification, transformers, BERT.",
     "https://www.coursera.org/specializations/natural-language-processing","Advanced",4.7,"NLP"),
    # Git
    ("Git & GitHub Complete Guide","Udemy",       "Version control, branching, collaboration.",
     "https://www.udemy.com/course/git-and-github-bootcamp/","Beginner",  4.7, "Git"),
]


# ─────────────────────────────────────────────────────────────────────────────
# Main seed function
# ─────────────────────────────────────────────────────────────────────────────
def seed_database():
    """Seed canonical IT skills, demo job roles, and sample courses. Idempotent."""

    # 1 — Skills
    skills: dict[str, Skill] = {}
    for name, category in SKILL_DEFS.items():
        skills[name] = _get_or_create_skill(name, category)
    db.session.commit()
    print(f"  Skills seeded: {len(skills)}")

    # 2 — Job Roles + Role-Skill Mappings
    roles_created = 0
    for role_name, role_data in ROLE_REQUIREMENTS.items():
        role = _get_or_create_role(
            role_name,
            f"demo:{role_name.lower().replace(' ', '_')}",
            role_data["desc"],
        )
        for skill_name, req_level, importance, rel_type in role_data["skills"]:
            # skill might not exist in canonical dict (e.g. "Node.js / Flask")
            sk = skills.get(skill_name) or _get_or_create_skill(skill_name, "General")
            _map_role_skill(role, sk, req_level, importance, rel_type)
        roles_created += 1
    db.session.commit()
    print(f"  Demo job roles seeded: {roles_created}")

    # 3 — Courses + Course-Skill Mappings
    courses_created = 0
    for title, provider, desc, url, diff, rating, skill_name in DEMO_COURSES:
        course = _get_or_create_course(title, provider, desc, url, diff, rating)
        sk = skills.get(skill_name) or _get_or_create_skill(skill_name, "General")
        _map_course_skill(course, sk, relevance=1.0)
        courses_created += 1
    db.session.commit()
    print(f"  Demo courses seeded: {courses_created}")

    print("Seed complete ✓  (Run 'flask ingest-data' for full ESCO + Coursera data)")
