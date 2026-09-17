# Dataset Repository — AI Skill Gap Analysis & Recommendation System

**Project Code:** MCA_MP_69  
**Institution:** Presidency University  
**System:** AI-Based Skill Gap Prediction & Learning Recommendation System  

---

## 📁 Directory Structure

```
Dataset/
├── README.md                                  # This documentation
├── onet/                                      # O*NET Competency & Occupational Taxonomy
│   ├── Knowledge.xlsx                         # O*NET Knowledge taxonomy (scales: IM, LV)
│   ├── Occupation_Data.xlsx                   # O*NET SOC occupation codes & descriptions
│   └── Work_Activities.xlsx                   # O*NET Generalized Work Activities (GWA)
├── coursera/                                  # Course & Learning Content Dataset
│   ├── Coursera.csv                           # 3,500+ courses with skills, difficulty & ratings
│   └── Coursera.zip                           # Backup compressed archive
├── students/                                  # Student Profiles & Academic Risk Data
│   ├── Student_Profiles_Indian_Names.xlsx     # Student demographics, technical skills & ratings
│   └── risk_analysis/                         # Subject/Topic academic risk evaluation
│       ├── student_data.csv                   # Historical student performance data
│       ├── train.csv                          # Training split for risk classifier
│       ├── test.csv                           # Evaluation split for risk classifier
│       └── student-at-risk-subject-topic-risk-analysis.zip
└── esco/                                      # European Skills, Competences & Occupations (v1.2.1)
    ├── classification_en_csv/                 # 19 official ESCO CSV files
    └── esco_v1.2.1.zip                        # Compressed archive
```

---

## 📊 Dataset Catalog & Usage

### 1. O*NET Taxonomy (`Dataset/onet/`)
* **Source:** U.S. Department of Labor / O*NET Resource Center (v27+)
* **Files:**
  * `Knowledge.xlsx`: Defines required knowledge domains across 1,000+ SOC occupations. Key columns: `O*NET-SOC Code`, `Element Name`, `Scale ID` (`IM` = Importance [1–5], `LV` = Level [0–7]), `Data Value`.
  * `Occupation_Data.xlsx`: Standard Occupational Classification (SOC) titles, descriptions, and code mappings.
  * `Work_Activities.xlsx`: Generalized Work Activities (GWA) for hands-on operational competencies.
* **Role in System:**
  * Maps competencies to standardized job roles.
  * Level ($LV$) is normalized to $1..5$ ($proficiency = req\_level \times 20$).
  * Importance ($IM$) is normalized to $[0.1, 1.0]$.
  * Filterable by category (`technical`, `knowledge`, `activity`).

---

### 2. Coursera Course Catalog (`Dataset/coursera/`)
* **Source:** Coursera Course Dataset (Kaggle)
* **Files:**
  * `Coursera.csv`: 3,522 rows covering Course Name, University, Difficulty Level, Rating, Course URL, Description, and Skills.
* **Role in System:**
  * Powers the hybrid course recommender engine (`services/recommender.py`).
  * Ingested by `data/ingest.py` to populate the `courses` and `course_skills` tables.
  * Courses are filtered for IT relevance and matched against identified student skill gaps.

---

### 3. Student Profiles & Risk Data (`Dataset/students/`)
* **Files:**
  * `Student_Profiles_Indian_Names.xlsx`: 20+ realistic student records with Indian names, degrees, specializations, self-reported skills, and proficiency ratings ($1..5$).
  * `risk_analysis/`: Academic risk classification dataset covering student study hours, previous topic test scores, and at-risk labels (`student_data.csv`, `train.csv`, `test.csv`).
* **Role in System:**
  * Ingested into `students` and `student_skills` tables during seed/ingest.
  * Supplies baseline profiles for testing skill gap detection, reassessment, and career path generation.

---

### 4. ESCO v1.2.1 Classification (`Dataset/esco/`)
* **Source:** European Commission ESCO Portal (v1.2.1)
* **Files:** 19 classification CSVs including:
  * `occupations_en.csv`: 3,000+ standardized European occupations.
  * `skills_en.csv`: 13,800+ standardized skills/competences.
  * `occupationSkillRelations_en.csv`: Essential vs optional skill mappings per occupation.
* **Role in System:**
  * Ingested into `job_roles`, `skills`, and `job_skills` tables.
  * Provides granular skill definitions linked to international standard identifiers (ESCO URIs).

---

## 🔄 ETL Pipeline Integration

To ingest all datasets into the backend database, run from the backend directory:
```bash
cd AI_Skill_Gap_Backend_Implementation
source .venv/bin/activate
flask ingest-data
```
The ingestion script automatically locates datasets using the clean directory paths, while maintaining full backward-compatibility with environment variable overrides in `.env`.
