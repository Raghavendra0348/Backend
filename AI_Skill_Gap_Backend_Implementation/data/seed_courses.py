"""
data/seed_courses.py — Curated learning resources for every skill in the 15-role taxonomy.

Ensures that every role skill has at least 2 courses mapped, enabling the
learning path generator and recommendation engine to produce meaningful results.

Run via Flask CLI:
    flask --app app seed-courses
"""
from extensions import db
from models import Course, CourseSkill, Skill


# ─────────────────────────────────────────────────────────────────────────────
# Curated Courses — Real platforms, realistic titles, multi-skill coverage
# ─────────────────────────────────────────────────────────────────────────────
CURATED_COURSES = [
    # ═══════════════════════════════════════════════════════════════════════════
    # WEB DEVELOPMENT FUNDAMENTALS
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "HTML, CSS, and Javascript for Web Developers",
        "provider": "Johns Hopkins University (Coursera)",
        "url": "https://www.coursera.org/learn/html-css-javascript-for-web-developers",
        "difficulty": "Beginner",
        "rating": 4.7,
        "description": "Learn the essential tools for front-end web development. From HTML5 semantic tags and CSS3 layouts to JavaScript DOM manipulation.",
        "skills": {"HTML5": 1.0, "CSS3": 1.0, "JavaScript": 0.9, "Responsive Web Design": 0.7},
    },
    {
        "title": "Advanced CSS and Sass: Flexbox, Grid, Animations",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/advanced-css-and-sass/",
        "difficulty": "Intermediate",
        "rating": 4.8,
        "description": "Master advanced CSS concepts including Flexbox, CSS Grid, animations, and Sass preprocessor for modern responsive layouts.",
        "skills": {"CSS3": 1.0, "Responsive Web Design": 0.9, "Frontend Performance": 0.6},
    },
    {
        "title": "Responsive Web Design Certification",
        "provider": "freeCodeCamp",
        "url": "https://www.freecodecamp.org/learn/2022/responsive-web-design/",
        "difficulty": "Beginner",
        "rating": 4.6,
        "description": "Build 20+ responsive web projects. Master HTML5, CSS3, Flexbox, Grid, accessibility, and responsive design principles.",
        "skills": {"HTML5": 1.0, "CSS3": 1.0, "Responsive Web Design": 1.0, "Web Accessibility": 0.8},
    },
    {
        "title": "Web Accessibility by Google",
        "provider": "Google (Udacity)",
        "url": "https://www.udacity.com/course/web-accessibility--ud891",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Learn how to build accessible web applications following WCAG guidelines, ARIA roles, and semantic HTML best practices.",
        "skills": {"Web Accessibility": 1.0, "WCAG Accessibility": 1.0, "HTML5": 0.5},
    },
    {
        "title": "WCAG 2.1 Compliance: Building Accessible Web Applications",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/web-accessibility-getting-started",
        "difficulty": "Intermediate",
        "rating": 4.3,
        "description": "Master WCAG 2.1 guidelines, screen reader testing, keyboard navigation, and accessibility auditing tools.",
        "skills": {"WCAG Accessibility": 1.0, "Web Accessibility": 0.9},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # JAVASCRIPT & TYPESCRIPT
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "The Complete JavaScript Course 2024: From Zero to Expert",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/the-complete-javascript-course/",
        "difficulty": "Beginner",
        "rating": 4.7,
        "description": "Master JavaScript with projects, challenges, and theory. ES6+, OOP, async/await, APIs, and modern tooling.",
        "skills": {"JavaScript": 1.0, "REST APIs": 0.6, "Data Structures & Algorithms": 0.4},
    },
    {
        "title": "Understanding TypeScript",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/understanding-typescript/",
        "difficulty": "Intermediate",
        "rating": 4.7,
        "description": "Deep dive into TypeScript: types, generics, decorators, modules, and integration with React and Node.js projects.",
        "skills": {"TypeScript": 1.0, "JavaScript": 0.5},
    },
    {
        "title": "TypeScript for Professionals",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/typescript-for-professionals/",
        "difficulty": "Advanced",
        "rating": 4.6,
        "description": "Advanced TypeScript patterns, utility types, conditional types, mapped types, and enterprise-scale TypeScript architecture.",
        "skills": {"TypeScript": 1.0, "Design Patterns": 0.5, "Software Architecture": 0.3},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # REACT & FRONTEND FRAMEWORKS
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "React - The Complete Guide (incl Hooks, React Router, Redux)",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/react-the-complete-guide-incl-redux/",
        "difficulty": "Intermediate",
        "rating": 4.6,
        "description": "Build powerful React applications. Covers hooks, context, Redux, routing, testing, Next.js, and deployment.",
        "skills": {"React": 1.0, "State Management": 0.9, "JavaScript": 0.6, "TypeScript": 0.4},
    },
    {
        "title": "Advanced React Patterns and Best Practices",
        "provider": "Frontend Masters",
        "url": "https://frontendmasters.com/courses/advanced-react-patterns/",
        "difficulty": "Advanced",
        "rating": 4.7,
        "description": "Master advanced React patterns: compound components, render props, hooks patterns, and performance optimization.",
        "skills": {"React": 1.0, "State Management": 0.8, "Frontend Performance": 0.7, "Design Systems": 0.5},
    },
    {
        "title": "Design Systems with React and Storybook",
        "provider": "Frontend Masters",
        "url": "https://frontendmasters.com/courses/design-systems/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Build a complete design system from scratch with React, Storybook, styled-components, and design tokens.",
        "skills": {"Design Systems": 1.0, "React": 0.7, "CSS3": 0.5},
    },
    {
        "title": "Tailwind CSS From Scratch",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/tailwind-from-scratch/",
        "difficulty": "Beginner",
        "rating": 4.6,
        "description": "Learn Tailwind CSS utility-first framework, responsive design, and building modern UI components.",
        "skills": {"Tailwind CSS / UI Libraries": 1.0, "CSS3": 0.5, "Responsive Web Design": 0.6},
    },
    {
        "title": "Tailwind CSS and UI Libraries Masterclass",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/tailwind-css-masterclass/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Advanced Tailwind CSS: custom plugins, component libraries, shadcn/ui, and enterprise design systems.",
        "skills": {"Tailwind CSS / UI Libraries": 1.0, "Design Systems": 0.7, "Frontend Performance": 0.4},
    },
    {
        "title": "State Management in React: Context, Redux, and Zustand",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/react-state-management/",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "Master state management patterns in React: useState, useReducer, Context API, Redux Toolkit, and Zustand.",
        "skills": {"State Management": 1.0, "React": 0.7},
    },
    {
        "title": "Figma to Code: From Design to Production",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/figma-to-code/",
        "difficulty": "Intermediate",
        "rating": 4.3,
        "description": "Transform Figma designs into pixel-perfect code using HTML, CSS, React, and design handoff best practices.",
        "skills": {"Figma-to-Code": 1.0, "CSS3": 0.6, "React": 0.5, "Design Systems": 0.4},
    },
    {
        "title": "Mobile-First Responsive Design with CSS",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/mobile-first-responsive-design",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "Learn mobile-first design strategies, media queries, touch interactions, and progressive enhancement.",
        "skills": {"Mobile-First Development": 1.0, "Responsive Web Design": 0.8, "CSS3": 0.5},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # WEB SECURITY & PERFORMANCE
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Web Security: OWASP Top 10 and Beyond",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/web-security-owasp/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Master web security: OWASP Top 10, XSS, CSRF, SQL injection, authentication security, and penetration testing.",
        "skills": {"Web Security / OWASP": 1.0, "Cybersecurity Fundamentals": 0.5},
    },
    {
        "title": "Web Performance Optimization with Lighthouse",
        "provider": "Google (Udacity)",
        "url": "https://www.udacity.com/course/website-performance-optimization--ud884",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "Optimize web performance: critical rendering path, lazy loading, code splitting, caching strategies, and Core Web Vitals.",
        "skills": {"Web Performance Optimization": 1.0, "Frontend Performance": 0.9, "Browser DevTools": 0.6},
    },
    {
        "title": "Chrome DevTools Masterclass",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/chrome-devtools/",
        "difficulty": "Beginner",
        "rating": 4.3,
        "description": "Master Chrome DevTools: debugging, performance profiling, network analysis, memory leaks, and accessibility audits.",
        "skills": {"Browser DevTools": 1.0, "Debugging & Profiling": 0.6, "Web Performance Optimization": 0.4},
    },
    {
        "title": "Web Testing with Cypress and Playwright",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/cypress-web-testing/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "End-to-end web testing with Cypress and Playwright: component testing, API testing, and CI/CD integration.",
        "skills": {"Web Testing": 1.0, "Playwright / Cypress": 0.9, "Test Automation": 0.7},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # NODE.JS & BACKEND JAVASCRIPT
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "The Complete Node.js Developer Course",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/the-complete-nodejs-developer-course-2/",
        "difficulty": "Intermediate",
        "rating": 4.6,
        "description": "Build REST APIs with Node.js, Express, MongoDB, JWT authentication, and deploy to production.",
        "skills": {"Node.js": 1.0, "REST API Development": 0.9, "Express.js / Fastify": 0.8, "Authentication": 0.6, "Authorization": 0.5},
    },
    {
        "title": "Node.js, Express, MongoDB & More: The Complete Bootcamp",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/nodejs-express-mongodb-bootcamp/",
        "difficulty": "Intermediate",
        "rating": 4.7,
        "description": "RESTful API design, authentication, security, data modeling, and production deployment with Node.js.",
        "skills": {"Node.js": 1.0, "Express.js / Fastify": 1.0, "REST APIs": 0.8, "Authentication": 0.7},
    },
    {
        "title": "Advanced Node.js: Scaling Applications",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/nodejs-advanced",
        "difficulty": "Advanced",
        "rating": 4.4,
        "description": "Advanced Node.js: clustering, worker threads, streams, microservices patterns, and performance optimization.",
        "skills": {"Node.js": 1.0, "Backend Performance Optimization": 0.8, "Microservices": 0.6, "Scalability": 0.5},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # PYTHON PROGRAMMING
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Python for Everybody Specialization",
        "provider": "University of Michigan (Coursera)",
        "url": "https://www.coursera.org/specializations/python",
        "difficulty": "Beginner",
        "rating": 4.8,
        "description": "Learn Python from scratch: data structures, web scraping, databases, and data visualization.",
        "skills": {"Python": 1.0, "SQL": 0.5, "Data Visualization": 0.4},
    },
    {
        "title": "Python 3: Deep Dive (Parts 1-4)",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/python-3-deep-dive-part-1/",
        "difficulty": "Advanced",
        "rating": 4.8,
        "description": "Master Python internals: closures, decorators, generators, metaclasses, context managers, and async programming.",
        "skills": {"Python": 1.0, "Data Structures & Algorithms": 0.5},
    },
    {
        "title": "Automate the Boring Stuff with Python",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/automate/",
        "difficulty": "Beginner",
        "rating": 4.7,
        "description": "Practical Python automation: file handling, web scraping, spreadsheets, email, and task scheduling.",
        "skills": {"Python": 0.9, "Python Automation": 1.0, "Bash Scripting": 0.3},
    },
    {
        "title": "Python Automation for DevOps",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/python-automation-devops",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "Automate infrastructure tasks with Python: AWS Boto3, API calls, log parsing, and monitoring scripts.",
        "skills": {"Python Automation": 1.0, "Python": 0.7, "AWS / Azure / GCP": 0.4, "Monitoring & Observability": 0.3},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # JAVA PROGRAMMING
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Java Programming and Software Engineering Fundamentals",
        "provider": "Duke University (Coursera)",
        "url": "https://www.coursera.org/specializations/java-programming",
        "difficulty": "Beginner",
        "rating": 4.6,
        "description": "Learn Java programming, object-oriented design, data structures, and software engineering principles.",
        "skills": {"Java": 1.0, "Data Structures & Algorithms": 0.7, "Software Architecture": 0.3},
    },
    {
        "title": "Java Spring Boot Microservices",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/spring-boot-microservices/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Build production microservices with Spring Boot, Spring Cloud, Docker, and Kubernetes.",
        "skills": {"Java / Spring Boot": 1.0, "Microservices": 0.9, "Docker": 0.6, "REST API Development": 0.7},
    },
    {
        "title": "Java / Android App Development",
        "provider": "Google (Coursera)",
        "url": "https://www.coursera.org/specializations/android-app-development",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Build Android applications with Java: activities, fragments, Room database, and Material Design.",
        "skills": {"Java / Android": 1.0, "Mobile UI/UX": 0.7, "Material Design": 0.6, "SQLite": 0.5},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # C++ / OOP
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Beginning C++ Programming — From Beginner to Beyond",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/beginning-c-plus-plus-programming/",
        "difficulty": "Beginner",
        "rating": 4.6,
        "description": "Master C++ fundamentals: OOP, templates, STL, pointers, memory management, and modern C++17 features.",
        "skills": {"C++ / OOP": 1.0, "Data Structures & Algorithms": 0.5},
    },
    {
        "title": "C++ Design Patterns and Object-Oriented Programming",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/patterns-cplusplus/",
        "difficulty": "Advanced",
        "rating": 4.5,
        "description": "Implement Gang of Four design patterns in modern C++: SOLID principles, creational, structural, and behavioral patterns.",
        "skills": {"C++ / OOP": 1.0, "Design Patterns": 0.9, "Software Architecture": 0.5},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # DATA STRUCTURES & ALGORITHMS
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Algorithms and Data Structures Masterclass",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/js-algorithms-and-data-structures-masterclass/",
        "difficulty": "Intermediate",
        "rating": 4.7,
        "description": "Master algorithms: sorting, searching, graphs, trees, dynamic programming, and Big O analysis.",
        "skills": {"Data Structures & Algorithms": 1.0},
    },
    {
        "title": "Algorithms Specialization",
        "provider": "Stanford University (Coursera)",
        "url": "https://www.coursera.org/specializations/algorithms",
        "difficulty": "Advanced",
        "rating": 4.8,
        "description": "Stanford's algorithms course: divide and conquer, graph algorithms, greedy algorithms, dynamic programming, NP-completeness.",
        "skills": {"Data Structures & Algorithms": 1.0, "System Design": 0.3},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # SQL & DATABASES
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "The Complete SQL Bootcamp",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/the-complete-sql-bootcamp/",
        "difficulty": "Beginner",
        "rating": 4.7,
        "description": "Master SQL: queries, joins, aggregation, subqueries, views, stored procedures, and database design.",
        "skills": {"SQL": 1.0, "Database Schema Design": 0.6, "Database Normalization": 0.5},
    },
    {
        "title": "Advanced SQL for Data Engineers",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/advanced-sql-mysql/",
        "difficulty": "Advanced",
        "rating": 4.5,
        "description": "Advanced SQL: window functions, CTEs, query optimization, indexing strategies, and performance tuning.",
        "skills": {"SQL": 1.0, "Query Optimization": 1.0, "Indexing": 0.8, "Database Schema Design": 0.6},
    },
    {
        "title": "PostgreSQL: From Zero to Hero",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/postgresql-from-zero-to-hero/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "PostgreSQL administration: installation, configuration, replication, backup, monitoring, and performance tuning.",
        "skills": {"PostgreSQL": 1.0, "PostgreSQL Administration": 1.0, "PostgreSQL / MySQL": 0.9, "Backup & Recovery": 0.6, "Replication": 0.5},
    },
    {
        "title": "MySQL Administration and DBA Essentials",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/mysql-database-administration/",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "MySQL server administration: user management, backup strategies, replication, performance monitoring, and security.",
        "skills": {"MySQL Administration": 1.0, "PostgreSQL / MySQL": 0.8, "Database Security": 0.7, "Backup & Recovery": 0.6, "Database Performance Monitoring": 0.7},
    },
    {
        "title": "Database Design and Normalization",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/database-design",
        "difficulty": "Beginner",
        "rating": 4.4,
        "description": "Learn relational database design: ER diagrams, normalization (1NF-BCNF), schema design, and data integrity.",
        "skills": {"Database Schema Design": 1.0, "Database Normalization": 1.0, "SQL": 0.5, "Data Modeling": 0.7},
    },
    {
        "title": "Database Architecture and Advanced Concepts",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/database-architecture",
        "difficulty": "Advanced",
        "rating": 4.3,
        "description": "Enterprise database architecture: sharding, partitioning, ACID, CAP theorem, and distributed database systems.",
        "skills": {"Database Architecture": 1.0, "High Availability": 0.7, "Scalability": 0.6, "Distributed Systems": 0.5},
    },
    {
        "title": "Database Migration Strategies and Tools",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/database-migration",
        "difficulty": "Intermediate",
        "rating": 4.2,
        "description": "Database migration: schema versioning with Flyway/Liquibase, zero-downtime migrations, and cloud migration strategies.",
        "skills": {"Database Migration": 1.0, "Database Schema Design": 0.5},
    },
    {
        "title": "Database Disaster Recovery and High Availability",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/disaster-recovery-databases",
        "difficulty": "Advanced",
        "rating": 4.3,
        "description": "Master disaster recovery: backup strategies, point-in-time recovery, replication, failover, and RPO/RTO planning.",
        "skills": {"Disaster Recovery": 1.0, "Backup & Recovery": 0.9, "High Availability": 0.8, "Replication": 0.7},
    },
    {
        "title": "SQLite for Mobile and Embedded Applications",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/sqlite-databases/",
        "difficulty": "Beginner",
        "rating": 4.3,
        "description": "Learn SQLite: creating databases, CRUD operations, joins, and integration with mobile applications.",
        "skills": {"SQLite": 1.0, "SQL": 0.6},
    },
    {
        "title": "Redis: The Complete Developer's Guide",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/redis-the-complete-developers-guide/",
        "difficulty": "Intermediate",
        "rating": 4.6,
        "description": "Master Redis: data structures, caching strategies, pub/sub, streams, Redis Cluster, and production deployment.",
        "skills": {"Redis / Caching": 1.0, "Caching": 0.9, "Backend Performance Optimization": 0.5},
    },
    {
        "title": "NoSQL Databases: MongoDB, DynamoDB, Cassandra",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/nosql-databases",
        "difficulty": "Intermediate",
        "rating": 4.3,
        "description": "Introduction to NoSQL databases: document stores, key-value, column-family, and graph databases.",
        "skills": {"NoSQL Databases": 1.0, "Data Modeling": 0.6},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # GIT & VERSION CONTROL
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Git Complete: The Definitive Guide",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/git-complete/",
        "difficulty": "Beginner",
        "rating": 4.5,
        "description": "Master Git: branching, merging, rebasing, cherry-picking, stashing, and GitHub collaboration workflows.",
        "skills": {"Git": 1.0},
    },
    {
        "title": "Advanced Git and GitHub for Developers",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/advanced-git",
        "difficulty": "Advanced",
        "rating": 4.4,
        "description": "Advanced Git: interactive rebase, bisect, reflog, submodules, hooks, and enterprise Git workflows.",
        "skills": {"Git": 1.0, "CI/CD": 0.3},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # REST APIs & BACKEND DEVELOPMENT
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "RESTful Web APIs: Design and Implementation",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/restful-web-apis/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Design and build RESTful APIs: HTTP methods, status codes, versioning, pagination, HATEOAS, and OpenAPI specs.",
        "skills": {"REST APIs": 1.0, "REST API Development": 1.0, "REST API Concepts": 1.0, "REST API Integration": 0.8},
    },
    {
        "title": "GraphQL: The Complete Guide",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/graphql-with-react-course/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Build GraphQL APIs: schemas, resolvers, queries, mutations, subscriptions, and Apollo Client integration.",
        "skills": {"GraphQL": 1.0, "REST / GraphQL": 0.9, "API Architecture": 0.5},
    },
    {
        "title": "API Design and Architecture",
        "provider": "Google Cloud (Coursera)",
        "url": "https://www.coursera.org/learn/api-design-and-fundamentals",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "API architecture patterns: REST, GraphQL, gRPC, API gateways, rate limiting, and API versioning strategies.",
        "skills": {"API Architecture": 1.0, "REST / GraphQL": 0.8, "REST API Development": 0.7, "Microservices Architecture": 0.4},
    },
    {
        "title": "FastAPI — Modern Python Web Framework",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/fastapi-the-complete-course/",
        "difficulty": "Intermediate",
        "rating": 4.6,
        "description": "Build high-performance APIs with FastAPI: async/await, Pydantic models, OAuth2, and automatic OpenAPI docs.",
        "skills": {"Python / FastAPI": 1.0, "REST API Development": 0.8, "Python": 0.6, "Authentication": 0.5, "Authorization": 0.5},
    },
    {
        "title": "JSON APIs and REST Integration Patterns",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/json-rest-api-integration",
        "difficulty": "Beginner",
        "rating": 4.3,
        "description": "JSON data formats, API integration patterns, error handling, and consuming RESTful services in client applications.",
        "skills": {"JSON / API Communication": 1.0, "REST API Integration": 0.9, "REST APIs": 0.5},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # DOCKER & CONTAINERS
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Docker and Kubernetes: The Complete Guide",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/docker-and-kubernetes-the-complete-guide/",
        "difficulty": "Intermediate",
        "rating": 4.6,
        "description": "Master Docker and Kubernetes: containers, images, docker-compose, K8s deployments, services, and ingress.",
        "skills": {"Docker": 1.0, "Kubernetes": 1.0, "CI/CD": 0.5},
    },
    {
        "title": "Docker Deep Dive",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/docker-deep-dive",
        "difficulty": "Advanced",
        "rating": 4.7,
        "description": "Advanced Docker: multi-stage builds, networking, volumes, security best practices, and Docker Swarm.",
        "skills": {"Docker": 1.0, "Linux / Shell Scripting": 0.3},
    },
    {
        "title": "Kubernetes for Developers",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/kubernetes-for-developers",
        "difficulty": "Advanced",
        "rating": 4.5,
        "description": "Kubernetes in depth: pods, services, deployments, ConfigMaps, secrets, Helm, and monitoring.",
        "skills": {"Kubernetes": 1.0, "Docker": 0.5, "Monitoring & Observability": 0.4},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # CI/CD & DEVOPS
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "CI/CD Pipelines with GitHub Actions, Jenkins, and GitLab",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/ci-cd-devops/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Build CI/CD pipelines: GitHub Actions, Jenkins, GitLab CI, automated testing, and deployment strategies.",
        "skills": {"CI/CD": 1.0, "Git": 0.5, "Docker": 0.4, "Test Automation": 0.4},
    },
    {
        "title": "Terraform: Infrastructure as Code",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/terraform-beginner-to-advanced/",
        "difficulty": "Intermediate",
        "rating": 4.6,
        "description": "Master Terraform: HCL syntax, providers, modules, state management, and multi-cloud infrastructure provisioning.",
        "skills": {"Terraform": 1.0, "Infrastructure as Code": 1.0, "AWS / Azure / GCP": 0.6},
    },
    {
        "title": "Infrastructure as Code: Terraform, Ansible, and Pulumi",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/infrastructure-as-code",
        "difficulty": "Advanced",
        "rating": 4.4,
        "description": "Advanced IaC: Terraform modules, Ansible playbooks, Pulumi, GitOps, and infrastructure testing.",
        "skills": {"Infrastructure as Code": 1.0, "Terraform": 0.8, "CI/CD": 0.4},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # LINUX & SHELL SCRIPTING
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Linux Administration Bootcamp",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/linux-administration-bootcamp/",
        "difficulty": "Beginner",
        "rating": 4.6,
        "description": "Linux system administration: users, permissions, systemd, package management, networking, and shell scripting.",
        "skills": {"Linux Administration": 1.0, "Linux / Shell Scripting": 0.9, "Bash Scripting": 0.8},
    },
    {
        "title": "Bash Scripting and Shell Programming",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/bash-scripting/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Master Bash scripting: variables, loops, functions, regular expressions, awk, sed, and automation scripts.",
        "skills": {"Bash Scripting": 1.0, "Linux / Shell Scripting": 1.0, "Linux Administration": 0.4},
    },
    {
        "title": "Advanced Linux: The Linux Kernel",
        "provider": "LinkedIn Learning",
        "url": "https://www.linkedin.com/learning/advanced-linux-the-linux-kernel",
        "difficulty": "Advanced",
        "rating": 4.3,
        "description": "Linux internals: kernel modules, system calls, process management, memory management, and kernel debugging.",
        "skills": {"Linux Administration": 1.0, "Linux Security": 0.5},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # CLOUD PLATFORMS (AWS / Azure / GCP)
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "AWS Certified Solutions Architect — Associate",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/aws-certified-solutions-architect-associate/",
        "difficulty": "Intermediate",
        "rating": 4.7,
        "description": "AWS fundamentals: EC2, S3, RDS, VPC, IAM, Lambda, CloudFormation, and architecture best practices.",
        "skills": {"AWS / Azure / GCP": 1.0, "Cloud Architecture": 0.9, "Cloud IAM": 0.8, "Scalability": 0.5, "High Availability": 0.5},
    },
    {
        "title": "Google Cloud Professional Cloud Architect",
        "provider": "Google Cloud (Coursera)",
        "url": "https://www.coursera.org/professional-certificates/gcp-cloud-architect",
        "difficulty": "Advanced",
        "rating": 4.6,
        "description": "GCP architecture: Compute Engine, GKE, Cloud SQL, BigQuery, IAM, and enterprise cloud design patterns.",
        "skills": {"AWS / Azure / GCP": 1.0, "Cloud Architecture": 1.0, "Cloud IAM": 0.7, "Cloud Data Services": 0.6},
    },
    {
        "title": "Cloud IAM and Identity Management",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/cloud-iam",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "Cloud identity and access management: IAM policies, roles, service accounts, multi-factor authentication, and SSO.",
        "skills": {"Cloud IAM": 1.0, "Identity & Access Management": 0.8, "Authentication": 0.5, "Authorization": 0.5},
    },
    {
        "title": "Cloud Data Services: BigQuery, Redshift, and Snowflake",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/cloud-data-services",
        "difficulty": "Intermediate",
        "rating": 4.3,
        "description": "Cloud data platforms: BigQuery, Redshift, Snowflake, data lakes, and serverless analytics.",
        "skills": {"Cloud Data Services": 1.0, "Data Warehousing": 0.7, "Data Lakes": 0.6, "SQL": 0.4},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # MONITORING, LOGGING & SRE
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Monitoring and Observability with Prometheus and Grafana",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/prometheus-grafana/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Set up monitoring: Prometheus metrics, Grafana dashboards, alerting, and application observability.",
        "skills": {"Monitoring & Observability": 1.0, "Logging": 0.5, "SRE Fundamentals": 0.4},
    },
    {
        "title": "Centralized Logging with ELK Stack",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/elk-stack-logging/",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "Build centralized logging: Elasticsearch, Logstash, Kibana, Filebeat, and log aggregation pipelines.",
        "skills": {"Logging": 1.0, "Monitoring & Observability": 0.6, "SIEM": 0.4},
    },
    {
        "title": "Site Reliability Engineering: Measuring and Managing Reliability",
        "provider": "Google Cloud (Coursera)",
        "url": "https://www.coursera.org/learn/site-reliability-engineering-slos",
        "difficulty": "Advanced",
        "rating": 4.5,
        "description": "SRE principles: SLIs/SLOs/SLAs, error budgets, toil reduction, incident management, and production readiness.",
        "skills": {"SRE Fundamentals": 1.0, "Monitoring & Observability": 0.7, "High Availability": 0.5, "Scalability": 0.4},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # NETWORKING
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "CompTIA Network+ Certification Course",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/comptia-network-certification/",
        "difficulty": "Beginner",
        "rating": 4.6,
        "description": "Complete networking: TCP/IP, DNS, DHCP, routing, switching, VLANs, subnetting, and network troubleshooting.",
        "skills": {"TCP/IP": 1.0, "TCP/IP Networking": 1.0, "DNS": 1.0, "DHCP": 1.0, "Routing": 0.9, "Switching": 0.9, "VLAN": 0.7, "Network Troubleshooting": 0.8},
    },
    {
        "title": "Network Security and Firewalls",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/network-security",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "Network security: firewalls, IDS/IPS, VPN technologies, ACLs, and network segmentation.",
        "skills": {"Network Security": 1.0, "Firewalls": 1.0, "VPN": 0.9, "Network Monitoring": 0.5},
    },
    {
        "title": "Advanced Network Troubleshooting and Monitoring",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/network-troubleshooting",
        "difficulty": "Advanced",
        "rating": 4.3,
        "description": "Network troubleshooting: Wireshark, packet analysis, SNMP monitoring, and performance diagnostics.",
        "skills": {"Network Troubleshooting": 1.0, "Network Monitoring": 1.0, "TCP/IP": 0.5},
    },
    {
        "title": "VPN Technologies and Implementation",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/vpn-technologies",
        "difficulty": "Intermediate",
        "rating": 4.2,
        "description": "VPN protocols: IPSec, SSL/TLS VPN, WireGuard, site-to-site and remote access VPN configurations.",
        "skills": {"VPN": 1.0, "Network Security": 0.6, "SSL/TLS": 0.5},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # WINDOWS SERVER & ACTIVE DIRECTORY
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Windows Server Administration Fundamentals",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/windows-server-administration/",
        "difficulty": "Beginner",
        "rating": 4.4,
        "description": "Windows Server: installation, Active Directory, Group Policy, DNS, DHCP, and user management.",
        "skills": {"Windows Server Administration": 1.0, "Active Directory": 0.9, "DNS": 0.5, "DHCP": 0.5},
    },
    {
        "title": "Active Directory and Group Policy Deep Dive",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/active-directory-deep-dive",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Active Directory: domain controllers, OUs, GPOs, trusts, replication, and AD security best practices.",
        "skills": {"Active Directory": 1.0, "Windows Server Administration": 0.7, "Identity & Access Management": 0.5},
    },
    {
        "title": "PowerShell for Systems Administrators",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/powershell-for-sysadmins/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "PowerShell automation: cmdlets, scripting, Active Directory management, remote administration, and DSC.",
        "skills": {"PowerShell": 1.0, "Windows Server Administration": 0.5, "Active Directory": 0.4},
    },
    {
        "title": "Windows Security Hardening",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/windows-security-hardening",
        "difficulty": "Advanced",
        "rating": 4.3,
        "description": "Windows security: hardening, auditing, Windows Defender, AppLocker, BitLocker, and security baselines.",
        "skills": {"Windows Security": 1.0, "Windows Server Administration": 0.5, "Security Compliance": 0.4},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # CYBERSECURITY
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Cybersecurity Fundamentals Specialization",
        "provider": "IBM (Coursera)",
        "url": "https://www.coursera.org/specializations/intro-cyber-security",
        "difficulty": "Beginner",
        "rating": 4.6,
        "description": "Cybersecurity foundations: threat landscape, security controls, risk management, and security operations.",
        "skills": {"Cybersecurity Fundamentals": 1.0, "Network Security": 0.6, "Threat Detection": 0.5},
    },
    {
        "title": "Vulnerability Assessment and Penetration Testing",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/vulnerability-assessment/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Vulnerability scanning: Nmap, Nessus, OWASP ZAP, penetration testing methodology, and remediation.",
        "skills": {"Vulnerability Assessment": 1.0, "Cybersecurity Fundamentals": 0.6, "Web Security / OWASP": 0.5},
    },
    {
        "title": "Incident Response and Digital Forensics",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/incident-response",
        "difficulty": "Advanced",
        "rating": 4.4,
        "description": "Incident response: NIST framework, containment, eradication, recovery, forensic analysis, and post-incident review.",
        "skills": {"Incident Response": 1.0, "Threat Detection": 0.8, "Security Log Analysis": 0.6},
    },
    {
        "title": "SIEM with Splunk: Security Information and Event Management",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/siem-splunk/",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "SIEM implementation: Splunk, log correlation, alert rules, dashboards, and security event investigation.",
        "skills": {"SIEM": 1.0, "Security Log Analysis": 0.9, "Logging": 0.5, "Threat Detection": 0.5},
    },
    {
        "title": "Cryptography and SSL/TLS",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/crypto",
        "difficulty": "Intermediate",
        "rating": 4.6,
        "description": "Applied cryptography: symmetric/asymmetric encryption, hashing, digital signatures, PKI, SSL/TLS, and certificate management.",
        "skills": {"Cryptography": 1.0, "SSL/TLS": 1.0, "Network Security": 0.4},
    },
    {
        "title": "Identity and Access Management (IAM)",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/identity-access-management",
        "difficulty": "Intermediate",
        "rating": 4.3,
        "description": "IAM principles: authentication, authorization, SSO, MFA, RBAC, and zero-trust architecture.",
        "skills": {"Identity & Access Management": 1.0, "Authentication": 0.8, "Authorization": 0.8, "Cloud IAM": 0.5},
    },
    {
        "title": "Linux Security and Hardening",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/linux-security-hardening",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "Linux security: SELinux, AppArmor, iptables, SSH hardening, file permissions, and security auditing.",
        "skills": {"Linux Security": 1.0, "Linux Administration": 0.6, "Firewalls": 0.4},
    },
    {
        "title": "Security Compliance: ISO 27001, SOC 2, GDPR",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/security-compliance/",
        "difficulty": "Intermediate",
        "rating": 4.2,
        "description": "Security compliance frameworks: ISO 27001, SOC 2, GDPR, PCI-DSS, HIPAA, and audit preparation.",
        "skills": {"Security Compliance": 1.0, "Security Architecture": 0.4},
    },
    {
        "title": "Security Architecture and Design",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/security-architecture",
        "difficulty": "Advanced",
        "rating": 4.4,
        "description": "Security architecture: threat modeling, defense in depth, zero-trust, security patterns, and risk assessment.",
        "skills": {"Security Architecture": 1.0, "Cybersecurity Fundamentals": 0.5, "Cloud Architecture": 0.4},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # DATA SCIENCE & MACHINE LEARNING
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Statistics for Data Science and Business Analysis",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/statistics-for-data-science-and-business-analysis/",
        "difficulty": "Beginner",
        "rating": 4.5,
        "description": "Statistics fundamentals: descriptive statistics, probability, distributions, hypothesis testing, and regression.",
        "skills": {"Statistics": 1.0, "Probability": 0.9, "Data Visualization": 0.3},
    },
    {
        "title": "Probability and Statistics for Data Science",
        "provider": "MIT (edX)",
        "url": "https://www.edx.org/learn/probability/mit-probability",
        "difficulty": "Intermediate",
        "rating": 4.7,
        "description": "Mathematical probability: random variables, distributions, Bayes theorem, Markov chains, and statistical inference.",
        "skills": {"Probability": 1.0, "Statistics": 0.8},
    },
    {
        "title": "Data Analysis with Pandas and NumPy",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/data-analysis-with-python",
        "difficulty": "Beginner",
        "rating": 4.6,
        "description": "Data manipulation with Pandas and NumPy: DataFrames, Series, merging, groupby, and statistical operations.",
        "skills": {"Pandas": 1.0, "NumPy": 1.0, "Data Cleaning": 0.7, "Python": 0.5},
    },
    {
        "title": "Advanced Pandas: Data Wrangling and Analysis",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/advanced-pandas/",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "Advanced Pandas techniques: MultiIndex, pivot tables, time series, text processing, and performance optimization.",
        "skills": {"Pandas": 1.0, "Data Cleaning": 0.8, "Feature Engineering": 0.5},
    },
    {
        "title": "Data Cleaning and Preprocessing in Python",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/data-cleaning",
        "difficulty": "Beginner",
        "rating": 4.3,
        "description": "Data cleaning techniques: handling missing values, outliers, duplicates, encoding, scaling, and validation.",
        "skills": {"Data Cleaning": 1.0, "Pandas": 0.6, "Feature Engineering": 0.5, "Python": 0.4},
    },
    {
        "title": "Feature Engineering for Machine Learning",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/feature-engineering-for-machine-learning/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Feature engineering: encoding, imputation, feature creation, selection, and transformation techniques.",
        "skills": {"Feature Engineering": 1.0, "Machine Learning": 0.6, "Scikit-learn": 0.4},
    },
    {
        "title": "Scikit-learn: Machine Learning in Python",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/machine-learning-with-python",
        "difficulty": "Intermediate",
        "rating": 4.6,
        "description": "Machine learning with Scikit-learn: classification, regression, clustering, pipelines, and model evaluation.",
        "skills": {"Scikit-learn": 1.0, "Machine Learning": 0.9, "Model Evaluation": 0.7, "Python": 0.5},
    },
    {
        "title": "Machine Learning by Stanford University",
        "provider": "Stanford University (Coursera)",
        "url": "https://www.coursera.org/learn/machine-learning",
        "difficulty": "Intermediate",
        "rating": 4.9,
        "description": "Andrew Ng's ML course: linear/logistic regression, neural networks, SVMs, unsupervised learning, and recommender systems.",
        "skills": {"Machine Learning": 1.0, "Machine Learning Algorithms": 0.9, "Statistics": 0.5, "Python": 0.4},
    },
    {
        "title": "Machine Learning Algorithms: Supervised and Unsupervised",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/machine-learning-algorithms/",
        "difficulty": "Advanced",
        "rating": 4.5,
        "description": "Deep understanding of ML algorithms: decision trees, random forests, gradient boosting, SVMs, and ensemble methods.",
        "skills": {"Machine Learning Algorithms": 1.0, "Machine Learning": 0.8, "Model Evaluation": 0.6},
    },
    {
        "title": "Model Evaluation and Hyperparameter Tuning",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/model-evaluation",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "Model evaluation metrics, cross-validation, hyperparameter tuning with GridSearchCV, RandomizedSearchCV, and Optuna.",
        "skills": {"Model Evaluation": 1.0, "Hyperparameter Optimization": 1.0, "Scikit-learn": 0.5},
    },
    {
        "title": "Data Visualization with Python (Matplotlib, Seaborn, Plotly)",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/python-for-data-visualization",
        "difficulty": "Beginner",
        "rating": 4.5,
        "description": "Data visualization: Matplotlib, Seaborn, Plotly, interactive dashboards, and storytelling with data.",
        "skills": {"Data Visualization": 1.0, "Python": 0.5, "Pandas": 0.4},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # DEEP LEARNING & NLP
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Deep Learning Specialization",
        "provider": "DeepLearning.AI (Coursera)",
        "url": "https://www.coursera.org/specializations/deep-learning",
        "difficulty": "Advanced",
        "rating": 4.9,
        "description": "Deep learning fundamentals: neural networks, CNNs, RNNs, transformers, optimization, and regularization.",
        "skills": {"Deep Learning": 1.0, "Machine Learning": 0.7, "NLP / Computer Vision": 0.5},
    },
    {
        "title": "PyTorch for Deep Learning and Computer Vision",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/pytorch-for-deep-learning/",
        "difficulty": "Intermediate",
        "rating": 4.6,
        "description": "Build deep learning models with PyTorch: tensors, autograd, CNNs, transfer learning, and model deployment.",
        "skills": {"PyTorch": 1.0, "Deep Learning": 0.9, "NLP / Computer Vision": 0.5},
    },
    {
        "title": "TensorFlow Developer Certificate",
        "provider": "DeepLearning.AI (Coursera)",
        "url": "https://www.coursera.org/professional-certificates/tensorflow-in-practice",
        "difficulty": "Intermediate",
        "rating": 4.7,
        "description": "TensorFlow ecosystem: Keras, TF Data, TF Lite, model serving, and end-to-end ML pipeline.",
        "skills": {"TensorFlow": 1.0, "Deep Learning": 0.8, "Model Serving": 0.5},
    },
    {
        "title": "NLP Fundamentals with Python",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/natural-language-processing",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "NLP: text preprocessing, tokenization, word embeddings, sentiment analysis, named entity recognition, and transformers.",
        "skills": {"NLP Fundamentals": 1.0, "NLP / Computer Vision": 0.8, "Python": 0.4, "Machine Learning": 0.4},
    },
    {
        "title": "Model Serving and MLOps with TFX and Kubernetes",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/machine-learning-modeling-pipelines-in-production",
        "difficulty": "Advanced",
        "rating": 4.5,
        "description": "ML model serving: TensorFlow Serving, TorchServe, FastAPI endpoints, model monitoring, and A/B testing.",
        "skills": {"Model Serving": 1.0, "MLOps": 0.9, "MLOps Fundamentals": 0.9, "Docker": 0.5},
    },
    {
        "title": "MLOps: Machine Learning Operations",
        "provider": "DeepLearning.AI (Coursera)",
        "url": "https://www.coursera.org/specializations/machine-learning-engineering-for-production-mlops",
        "difficulty": "Advanced",
        "rating": 4.6,
        "description": "MLOps: ML pipelines, experiment tracking, model registry, CI/CD for ML, and production monitoring.",
        "skills": {"MLOps": 1.0, "MLOps Fundamentals": 1.0, "Model Serving": 0.7, "CI/CD": 0.4, "Docker": 0.4},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # DATA ENGINEERING
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Apache Spark with Python (PySpark)",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/spark-and-python-for-big-data-with-pyspark/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Big data processing with PySpark: RDDs, DataFrames, SparkSQL, MLlib, and Spark Streaming.",
        "skills": {"Apache Spark": 1.0, "Python": 0.5, "SQL": 0.4, "Data Pipelines": 0.5},
    },
    {
        "title": "Apache Kafka: Streaming Data Pipelines",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/apache-kafka/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Apache Kafka: producers, consumers, Kafka Streams, Connect, and real-time data pipeline architecture.",
        "skills": {"Apache Kafka": 1.0, "Data Pipelines": 0.8, "Message Queues": 0.7},
    },
    {
        "title": "Apache Airflow: Workflow Orchestration",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/the-complete-hands-on-course-to-master-apache-airflow/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Apache Airflow: DAGs, operators, sensors, XComs, task dependencies, and scheduling data pipelines.",
        "skills": {"Apache Airflow": 1.0, "Data Pipelines": 0.9, "ETL / ELT": 0.7, "Python": 0.4},
    },
    {
        "title": "ETL and Data Pipeline Design",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/etl-and-data-pipelines-shell-airflow-kafka",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "ETL/ELT patterns: batch vs streaming, data pipeline orchestration, error handling, and data quality checks.",
        "skills": {"ETL / ELT": 1.0, "Data Pipelines": 1.0, "Data Quality": 0.6, "Apache Airflow": 0.5},
    },
    {
        "title": "Data Warehousing and Dimensional Modeling",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/data-warehousing",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "Data warehouse design: star/snowflake schemas, fact/dimension tables, ETL, and OLAP queries.",
        "skills": {"Data Warehousing": 1.0, "Data Modeling": 0.9, "SQL": 0.5, "ETL / ELT": 0.5},
    },
    {
        "title": "Data Lakes and Lakehouse Architecture",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/data-lakes",
        "difficulty": "Advanced",
        "rating": 4.3,
        "description": "Data lake architecture: Delta Lake, Iceberg, partitioning, schema evolution, and lakehouse patterns.",
        "skills": {"Data Lakes": 1.0, "Data Warehousing": 0.5, "Cloud Data Services": 0.5},
    },
    {
        "title": "Data Modeling for Analytics and Engineering",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/data-modeling/",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "Data modeling: conceptual, logical, physical models, ER diagrams, normalization, and dimensional modeling.",
        "skills": {"Data Modeling": 1.0, "Database Schema Design": 0.7, "SQL": 0.4},
    },
    {
        "title": "Data Quality Engineering",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/data-quality",
        "difficulty": "Intermediate",
        "rating": 4.2,
        "description": "Data quality: validation rules, data profiling, anomaly detection, Great Expectations, and data governance.",
        "skills": {"Data Quality": 1.0, "Data Cleaning": 0.6, "Data Pipelines": 0.4},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # SOFTWARE ARCHITECTURE & DESIGN
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Software Architecture: Complete Guide",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/software-architecture-design/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Software architecture patterns: monolithic, microservices, event-driven, CQRS, and hexagonal architecture.",
        "skills": {"Software Architecture": 1.0, "Design Patterns": 0.7, "System Design": 0.6, "Microservices Architecture": 0.5},
    },
    {
        "title": "System Design Interview: The Complete Guide",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/system-design-interview/",
        "difficulty": "Advanced",
        "rating": 4.7,
        "description": "System design: load balancing, caching, CDN, message queues, database sharding, and distributed systems.",
        "skills": {"System Design": 1.0, "Scalability": 0.9, "High Availability": 0.8, "Caching": 0.7, "Message Queues": 0.6, "Distributed Systems": 0.8},
    },
    {
        "title": "Design Patterns in Modern Programming",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/design-patterns-python/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Gang of Four design patterns: SOLID principles, creational, structural, behavioral, and architectural patterns.",
        "skills": {"Design Patterns": 1.0, "Software Architecture": 0.6, "Architecture Design Patterns": 0.8},
    },
    {
        "title": "Microservices Architecture: The Complete Guide",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/microservices-architecture/",
        "difficulty": "Advanced",
        "rating": 4.5,
        "description": "Microservices: decomposition, API gateway, service mesh, saga pattern, CQRS, and event sourcing.",
        "skills": {"Microservices Architecture": 1.0, "Microservices": 0.9, "API Architecture": 0.7, "Message Queues": 0.5, "Docker": 0.4},
    },
    {
        "title": "Distributed Systems: Principles and Paradigms",
        "provider": "MIT (edX)",
        "url": "https://www.edx.org/learn/computer-science/mit-distributed-systems",
        "difficulty": "Advanced",
        "rating": 4.6,
        "description": "Distributed systems: consensus algorithms, replication, fault tolerance, and consistency models.",
        "skills": {"Distributed Systems": 1.0, "Fault Tolerance": 0.9, "Scalability": 0.7, "High Availability": 0.6},
    },
    {
        "title": "Architecture Design Patterns for Enterprise Systems",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/architecture-design-patterns",
        "difficulty": "Advanced",
        "rating": 4.4,
        "description": "Enterprise architecture patterns: layered, hexagonal, pipes and filters, broker, and blackboard patterns.",
        "skills": {"Architecture Design Patterns": 1.0, "Software Architecture": 0.8, "Design Patterns": 0.6},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # TESTING & QA
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Software Testing Fundamentals: ISTQB Foundation",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/istqb-foundation-level/",
        "difficulty": "Beginner",
        "rating": 4.5,
        "description": "ISTQB Foundation: testing principles, test levels, techniques, management, and tools.",
        "skills": {"Software Testing Fundamentals": 1.0, "Test Case Design": 0.8, "Test Planning": 0.7, "Manual Testing": 0.6},
    },
    {
        "title": "Test Case Design and Test Planning",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/software-testing-test-case-design/",
        "difficulty": "Beginner",
        "rating": 4.3,
        "description": "Test case design techniques: equivalence partitioning, boundary analysis, decision tables, and state transition testing.",
        "skills": {"Test Case Design": 1.0, "Test Planning": 0.9, "Manual Testing": 0.7, "Functional Testing": 0.5},
    },
    {
        "title": "Manual Testing and Functional Testing",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/manual-software-testing/",
        "difficulty": "Beginner",
        "rating": 4.4,
        "description": "Manual and functional testing: test execution, defect reporting, regression testing, and exploratory testing.",
        "skills": {"Manual Testing": 1.0, "Functional Testing": 1.0, "Regression Testing": 0.8, "Bug Tracking / Jira": 0.6},
    },
    {
        "title": "API Testing with Postman and REST Assured",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/api-testing-with-postman/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "API testing: Postman collections, REST Assured, API automation, contract testing, and CI/CD integration.",
        "skills": {"API Testing": 1.0, "REST APIs": 0.5, "Test Automation": 0.5},
    },
    {
        "title": "Selenium WebDriver with Java — Complete Course",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/selenium-webdriver-java/",
        "difficulty": "Intermediate",
        "rating": 4.5,
        "description": "Selenium test automation: locators, waits, Page Object Model, TestNG, and CI/CD integration.",
        "skills": {"Selenium": 1.0, "Test Automation": 0.9, "Functional Testing": 0.5, "Regression Testing": 0.5},
    },
    {
        "title": "Playwright and Cypress: Modern E2E Testing",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/playwright-cypress-testing/",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "Modern E2E testing with Playwright and Cypress: parallel testing, visual regression, and CI/CD pipelines.",
        "skills": {"Playwright / Cypress": 1.0, "Test Automation": 0.8, "Web Testing": 0.7},
    },
    {
        "title": "Unit Testing and TDD in Python and Java",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/unit-testing-tdd/",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "Unit testing: pytest, JUnit, mocking, test-driven development, code coverage, and testing best practices.",
        "skills": {"Unit Testing": 1.0, "Test Automation": 0.6, "Software Testing Fundamentals": 0.4},
    },
    {
        "title": "Integration Testing Strategies",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/integration-testing",
        "difficulty": "Intermediate",
        "rating": 4.3,
        "description": "Integration testing: contract tests, API integration, database integration, and test environment management.",
        "skills": {"Integration Testing": 1.0, "API Testing": 0.6, "Test Planning": 0.4},
    },
    {
        "title": "Performance Testing with JMeter and k6",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/performance-testing-jmeter/",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "Performance testing: JMeter, k6, load testing, stress testing, and performance analysis.",
        "skills": {"Performance Testing": 1.0, "Load Testing": 1.0},
    },
    {
        "title": "Bug Tracking with Jira: Agile Project Management",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/jira-for-beginners/",
        "difficulty": "Beginner",
        "rating": 4.3,
        "description": "Jira for QA: issue tracking, bug reports, scrum boards, kanban boards, and agile workflows.",
        "skills": {"Bug Tracking / Jira": 1.0, "Agile / Scrum": 0.7},
    },
    {
        "title": "Debugging and Profiling: Performance Analysis",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/debugging-profiling",
        "difficulty": "Intermediate",
        "rating": 4.3,
        "description": "Debugging techniques: breakpoints, step debugging, memory profiling, CPU profiling, and performance analysis.",
        "skills": {"Debugging & Profiling": 1.0, "Browser DevTools": 0.4, "Frontend Performance": 0.3},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # AGILE & PROJECT MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Agile with Atlassian Jira",
        "provider": "Atlassian (Coursera)",
        "url": "https://www.coursera.org/learn/agile-atlassian-jira",
        "difficulty": "Beginner",
        "rating": 4.5,
        "description": "Agile project management with Jira: Scrum ceremonies, sprint planning, user stories, and retrospectives.",
        "skills": {"Agile / Scrum": 1.0, "Bug Tracking / Jira": 0.6, "User Stories": 0.5},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # MOBILE DEVELOPMENT
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Android Development with Kotlin",
        "provider": "Google (Coursera)",
        "url": "https://www.coursera.org/specializations/kotlin-for-java-developers",
        "difficulty": "Intermediate",
        "rating": 4.6,
        "description": "Build Android apps with Kotlin: coroutines, Jetpack Compose, Room, and ViewModel architecture.",
        "skills": {"Kotlin": 1.0, "Java / Android": 0.7, "Mobile UI/UX": 0.6, "Mobile State Management": 0.5},
    },
    {
        "title": "iOS Development with Swift",
        "provider": "Stanford University (YouTube)",
        "url": "https://www.youtube.com/playlist?list=PLpGHT1n4-mAsxuRxVPv7kj4HPMPcQVkHH",
        "difficulty": "Intermediate",
        "rating": 4.8,
        "description": "Stanford's CS193p: SwiftUI, MVVM, gestures, animations, persistence, and iOS development best practices.",
        "skills": {"Swift / iOS": 1.0, "Mobile UI/UX": 0.6, "Mobile State Management": 0.5},
    },
    {
        "title": "React Native — The Practical Guide",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/react-native-the-practical-guide/",
        "difficulty": "Intermediate",
        "rating": 4.6,
        "description": "Build cross-platform mobile apps with React Native: navigation, state management, native modules, and deployment.",
        "skills": {"React Native": 1.0, "Mobile UI/UX": 0.7, "Mobile State Management": 0.6, "REST API Integration": 0.5, "App Store / Google Play Deployment": 0.4},
    },
    {
        "title": "Flutter & Dart — The Complete Guide",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/learn-flutter-dart-to-build-ios-android-apps/",
        "difficulty": "Intermediate",
        "rating": 4.6,
        "description": "Flutter development: widgets, state management, networking, animations, and publishing to app stores.",
        "skills": {"Flutter": 1.0, "Mobile UI/UX": 0.6, "Mobile State Management": 0.5, "App Store / Google Play Deployment": 0.5},
    },
    {
        "title": "Material Design for Android Developers",
        "provider": "Google (Udacity)",
        "url": "https://www.udacity.com/course/material-design-for-android--ud862",
        "difficulty": "Intermediate",
        "rating": 4.3,
        "description": "Material Design: components, typography, color systems, motion, and Android UI implementation.",
        "skills": {"Material Design": 1.0, "Mobile UI/UX": 0.7},
    },
    {
        "title": "Mobile App Deployment: App Store and Google Play",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/mobile-app-deployment/",
        "difficulty": "Beginner",
        "rating": 4.2,
        "description": "Publish apps: App Store Connect, Google Play Console, signing, screenshots, metadata, and release management.",
        "skills": {"App Store / Google Play Deployment": 1.0},
    },
    {
        "title": "Push Notifications for iOS and Android",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/push-notifications",
        "difficulty": "Intermediate",
        "rating": 4.2,
        "description": "Push notifications: Firebase Cloud Messaging, APNs, notification channels, and rich notifications.",
        "skills": {"Push Notifications": 1.0, "Mobile UI/UX": 0.3},
    },
    {
        "title": "Mobile Security Best Practices",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/mobile-security",
        "difficulty": "Intermediate",
        "rating": 4.3,
        "description": "Mobile security: secure storage, certificate pinning, OWASP Mobile Top 10, and penetration testing.",
        "skills": {"Mobile Security": 1.0, "Mobile Testing": 0.4},
    },
    {
        "title": "Mobile Testing with Appium and XCTest",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/mobile-testing-appium/",
        "difficulty": "Intermediate",
        "rating": 4.3,
        "description": "Mobile test automation: Appium, XCTest, Espresso, UI testing, and mobile CI/CD pipelines.",
        "skills": {"Mobile Testing": 1.0, "Test Automation": 0.6},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # SYSTEMS ANALYSIS & REQUIREMENTS
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Requirements Engineering and Analysis",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/requirements-engineering",
        "difficulty": "Intermediate",
        "rating": 4.3,
        "description": "Requirements engineering: elicitation, analysis, specification, validation, and requirements management.",
        "skills": {"Requirements Engineering": 1.0, "Requirements Analysis": 1.0, "User Stories": 0.5, "Gap Analysis": 0.4},
    },
    {
        "title": "UML and System Modeling",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/uml-and-object-oriented-design/",
        "difficulty": "Intermediate",
        "rating": 4.3,
        "description": "UML diagrams: use case, class, sequence, activity, state, and component diagrams for system modeling.",
        "skills": {"UML": 1.0, "System Modeling": 1.0, "Software Architecture Analysis": 0.5},
    },
    {
        "title": "Business Process Modeling with BPMN 2.0",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/bpmn/",
        "difficulty": "Intermediate",
        "rating": 4.2,
        "description": "BPMN 2.0: process mapping, workflow analysis, gap analysis, and business process improvement.",
        "skills": {"Business Process Modeling": 1.0, "Gap Analysis": 0.8, "System Modeling": 0.5},
    },
    {
        "title": "System Integration Patterns and Strategies",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/system-integration",
        "difficulty": "Intermediate",
        "rating": 4.3,
        "description": "Enterprise integration patterns: messaging, APIs, middleware, ESB, and microservices integration.",
        "skills": {"System Integration": 1.0, "REST API Concepts": 0.6, "Microservices": 0.4},
    },
    {
        "title": "Technical Documentation and API Documentation",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/technical-writing",
        "difficulty": "Beginner",
        "rating": 4.4,
        "description": "Technical writing: API documentation, system specifications, user guides, and documentation tools.",
        "skills": {"Technical Documentation": 1.0, "REST API Concepts": 0.3},
    },
    {
        "title": "Software Architecture Analysis and Evaluation",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/software-architecture-analysis",
        "difficulty": "Advanced",
        "rating": 4.3,
        "description": "Architecture analysis: ATAM, quality attributes, tradeoff analysis, and architecture evaluation methods.",
        "skills": {"Software Architecture Analysis": 1.0, "Software Architecture": 0.7, "System Design": 0.5},
    },
    {
        "title": "User Acceptance Testing and Functional Testing",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/user-acceptance-testing/",
        "difficulty": "Beginner",
        "rating": 4.2,
        "description": "UAT planning, test case creation, defect management, sign-off criteria, and stakeholder communication.",
        "skills": {"User Acceptance Testing": 1.0, "Functional Testing": 0.7, "Test Planning": 0.5},
    },
    {
        "title": "Writing Effective User Stories",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/user-stories",
        "difficulty": "Beginner",
        "rating": 4.3,
        "description": "User stories: INVEST criteria, acceptance criteria, story mapping, and backlog grooming.",
        "skills": {"User Stories": 1.0, "Agile / Scrum": 0.5, "Requirements Analysis": 0.4},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # AUTHENTICATION & AUTHORIZATION
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Authentication and Authorization: OAuth 2.0 and JWT",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/oauth-2-simplified/",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "Auth protocols: OAuth 2.0, OpenID Connect, JWT, session management, RBAC, and API security.",
        "skills": {"Authentication": 1.0, "Authorization": 1.0, "JWT / OAuth": 1.0, "Web Security / OWASP": 0.4},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # MESSAGE QUEUES & CACHING
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Message Queues: RabbitMQ, Kafka, and SQS",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/message-queues/",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "Message queue systems: RabbitMQ, Apache Kafka, AWS SQS, pub/sub patterns, and event-driven architecture.",
        "skills": {"Message Queues": 1.0, "Apache Kafka": 0.6, "Microservices": 0.4},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # BACKUP & DISASTER RECOVERY
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Backup and Disaster Recovery Strategies",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/backup-disaster-recovery",
        "difficulty": "Intermediate",
        "rating": 4.3,
        "description": "Enterprise backup: 3-2-1 rule, cloud backup, disaster recovery planning, RTO/RPO, and business continuity.",
        "skills": {"Backup & Disaster Recovery": 1.0, "Disaster Recovery": 0.8, "Backup & Recovery": 0.7, "High Availability": 0.4},
    },

    # ═══════════════════════════════════════════════════════════════════════════
    # DATABASE SECURITY & PERFORMANCE
    # ═══════════════════════════════════════════════════════════════════════════
    {
        "title": "Database Security: Protecting Your Data",
        "provider": "Coursera",
        "url": "https://www.coursera.org/learn/database-security",
        "difficulty": "Intermediate",
        "rating": 4.3,
        "description": "Database security: access control, encryption, auditing, SQL injection prevention, and compliance.",
        "skills": {"Database Security": 1.0, "SQL": 0.4},
    },
    {
        "title": "Database Performance Monitoring and Tuning",
        "provider": "Pluralsight",
        "url": "https://www.pluralsight.com/courses/database-performance-monitoring",
        "difficulty": "Advanced",
        "rating": 4.4,
        "description": "Database performance: query analysis, execution plans, indexing strategies, and monitoring tools.",
        "skills": {"Database Performance Monitoring": 1.0, "Query Optimization": 0.8, "Indexing": 0.7},
    },
    {
        "title": "Query Optimization and Indexing Strategies",
        "provider": "Udemy",
        "url": "https://www.udemy.com/course/sql-query-optimization/",
        "difficulty": "Intermediate",
        "rating": 4.4,
        "description": "SQL query optimization: EXPLAIN plans, index types, join optimization, and partitioning strategies.",
        "skills": {"Query Optimization": 1.0, "Indexing": 1.0, "SQL": 0.5},
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Seeding Function
# ─────────────────────────────────────────────────────────────────────────────
def _get_or_create_skill(name: str) -> Skill:
    """Return existing Skill or create a new one (canonicalized)."""
    from services.skill_normalizer import canonicalize_skill_name
    canon = canonicalize_skill_name(name)
    name = (canon or name).strip()[:140]
    sk = Skill.query.filter(db.func.lower(Skill.name) == name.lower()).first()
    if not sk:
        sk = Skill(name=name, category="General", source="CANONICAL")
        db.session.add(sk)
        db.session.flush()
    return sk


def seed_curated_courses() -> dict:
    """
    Seed all curated courses into the database.
    Idempotent: skips courses that already exist (by title + provider).
    """
    from models import ImportBatch

    batch = ImportBatch(source="seed_courses", status="running")
    db.session.add(batch)
    db.session.commit()

    print("\n=== Seeding Curated Learning Resources ===")
    courses_created = 0
    course_skills_created = 0
    courses_skipped = 0
    skills_covered = set()

    try:
        for entry in CURATED_COURSES:
            title = entry["title"]
            provider = entry["provider"]

            # Skip if already exists
            existing = Course.query.filter_by(title=title, provider=provider).first()
            if existing:
                course = existing
                courses_skipped += 1
            else:
                course = Course(
                    title=title,
                    provider=provider,
                    url=entry.get("url", ""),
                    description=entry.get("description", ""),
                    difficulty_level=entry.get("difficulty", "Intermediate"),
                    rating=entry.get("rating", 4.0),
                    source="Curated",
                )
                db.session.add(course)
                db.session.flush()
                courses_created += 1

            # Map skills
            for skill_name, relevance in entry.get("skills", {}).items():
                skill = _get_or_create_skill(skill_name)
                skills_covered.add(skill.name)

                existing_cs = CourseSkill.query.filter_by(
                    course_id=course.id, skill_id=skill.id
                ).first()
                if not existing_cs:
                    db.session.add(CourseSkill(
                        course_id=course.id,
                        skill_id=skill.id,
                        relevance=relevance,
                    ))
                    course_skills_created += 1

        batch.finish(
            inserted=courses_created + course_skills_created,
            updated=0,
            skipped=courses_skipped,
        )
        db.session.commit()
        print(f"  {courses_created} new courses seeded")
        print(f"  {course_skills_created} new CourseSkill mappings created")
        print(f"  {len(skills_covered)} unique skills covered by curated courses")
        print(f"  Batch #{batch.id} recorded with status: {batch.status}")

        return {
            "batch_id": batch.id,
            "courses_created": courses_created,
            "course_skills_created": course_skills_created,
            "skills_covered": len(skills_covered),
        }
    except Exception as e:
        batch.finish(
            inserted=courses_created + course_skills_created,
            updated=0,
            skipped=courses_skipped,
            error=e,
        )
        db.session.commit()
        raise
