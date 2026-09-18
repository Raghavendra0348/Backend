# 🚀 AI Skill Gap Backend — Windows Setup Guide

A step-by-step guide to clone, configure, and run this project on a **Windows** machine.

---

## Prerequisites (Install These First)

### 1. Install Python 3.12+

1. Go to [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Download **Python 3.12.x** (or latest 3.12+)
3. Run the installer
4. ⚠️ **IMPORTANT**: Check the box **"Add Python to PATH"** at the bottom of the installer
5. Click **"Install Now"**
6. Verify installation — open **Command Prompt** (or PowerShell) and run:
   ```
   python --version
   ```

   You should see something like: `Python 3.12.x`

### 2. Install Git

1. Go to [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Download and install (use all default options)
3. Verify:
   ```
   git --version
   ```

### 3. Install MySQL

1. Go to [https://dev.mysql.com/downloads/installer/](https://dev.mysql.com/downloads/installer/)
2. Download **MySQL Installer for Windows**
3. During setup, install:
   - **MySQL Server**
   - **MySQL Workbench** (optional, for GUI management)
4. Set a root password during setup — **remember this password!**
5. Verify MySQL is running:
   ```
   mysql -u root -p
   ```

   Enter your password. If you see the `mysql>` prompt, it's working. Type `exit` to quit.

---

## Step-by-Step Setup

### Step 1: Clone the Repository

Open **Command Prompt** or **PowerShell** and run:

```bash
cd %USERPROFILE%\Desktop
git clone https://github.com/Raghavendra0348/Backend.git
cd Backend
```

Your folder structure should look like this:

```
Backend/
├── AI_Skill_Gap_Backend_Implementation/    ← Main application code
├── Dataset/                                ← ESCO, O*NET, Coursera, Student data
│   ├── esco/
│   ├── onet/
│   ├── coursera/
│   └── students/
├── ESCO dataset - v1.2.1 - .../           ← Legacy ESCO data (fallback)
└── docs/
```

---

### Step 2: Navigate to the Application Directory

```bash
cd AI_Skill_Gap_Backend_Implementation
```

All commands from here onward are run **inside this folder**.

---

### Step 3: Create a Python Virtual Environment

```bash
python -m venv .venv
```

### Step 4: Activate the Virtual Environment

**Command Prompt:**

```bash
.venv\Scripts\activate
```

**PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

> **PowerShell Error?** If you get an "execution policy" error, run this first:
>
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
>
> Then try the activate command again.

After activation, your prompt should show `(.venv)` at the beginning.

---

### Step 5: Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install Flask, SQLAlchemy, scikit-learn, spaCy, and all other required packages.

---

### Step 6: Create the MySQL Database

Open a **new** Command Prompt window (keep the venv one open) and run:

```bash
mysql -u root -p
```

Enter your MySQL root password, then run these SQL commands:

```sql
CREATE DATABASE skill_gap_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
SHOW DATABASES;
exit;
```

You should see `skill_gap_db` in the list.

---

### Step 7: Create the `.env` Configuration File

Go back to the terminal with `(.venv)` active. Create a file named `.env` in the `AI_Skill_Gap_Backend_Implementation` folder.

You can create it using Notepad:

```bash
notepad .env
```

Paste the following content and **edit the values marked with ⬅️**:

```env
SECRET_KEY=my-super-secret-key-change-this
DATABASE_URL=mysql+pymysql://root:YOUR_MYSQL_PASSWORD@127.0.0.1:3306/skill_gap_db
UPLOAD_DIR=storage/uploads
MODEL_PATH=ml/models/skill_gap_model.joblib
MAX_CONTENT_LENGTH=5242880
```

⬅️ **Replace `YOUR_MYSQL_PASSWORD`** with the actual MySQL root password you set during MySQL installation.

Save and close the file.

---

### Step 8: Initialize the Database (Run Migrations)

```bash
flask db upgrade
```

This applies all database migrations and creates the required tables.

---

### Step 9: Seed the Database with Data

Run these commands **in order**:

```bash
:: Step 9a — Create the 15 IT job roles with their core skills
flask sync-roles

:: Step 9b — Seed curated learning courses for each role
flask seed-courses

:: Step 9c — Ingest ESCO taxonomy data (skills, roles from EU classification)
flask ingest-data

:: Step 9d — Ingest O*NET competency data (knowledge + work activities)
flask ingest-onet
```

> ⏱️ `ingest-data` and `ingest-onet` may take a few minutes depending on your machine.

---

### Step 10: Create Required Directories

```bash
mkdir storage\uploads 2>nul
mkdir ml\models 2>nul
```

---

### Step 11: Run the Application 🎉

```bash
flask --app app run --debug
```

The server will start at: **http://127.0.0.1:5000**

Open this URL in your browser. You should see the application homepage.

---

## API Endpoints Quick Reference

| Endpoint                                  | Description                     |
| ----------------------------------------- | ------------------------------- |
| `http://127.0.0.1:5000/`                | Home page (UI)                  |
| `http://127.0.0.1:5000/skills`          | Skills & Resume Parser page     |
| `http://127.0.0.1:5000/learning`        | Learning Path & Recommendations |
| `http://127.0.0.1:5000/api/v1/health`   | API health check                |
| `http://127.0.0.1:5000/api/v1/students` | Students API                    |
| `http://127.0.0.1:5000/api/v1/roles`    | Job Roles API                   |
| `http://127.0.0.1:5000/api/v1/skills`   | Skills Catalog API              |

---

## Running Tests

Make sure your virtual environment is activated, then:

```bash
python -m pytest
```

Expected: **126 tests passed** ✅

To run a specific test file:

```bash
python -m pytest tests/test_v1_api.py -v
python -m pytest tests/test_recommender.py -v
```

---

## Troubleshooting

### ❌ `python` is not recognized

- Re-run the Python installer and make sure **"Add Python to PATH"** is checked
- Or use `py` instead of `python` (Windows Python Launcher)

### ❌ `mysql` is not recognized

- Add MySQL to your system PATH:
  1. Find your MySQL installation (usually `C:\Program Files\MySQL\MySQL Server 8.x\bin`)
  2. Add this path to your system's **Environment Variables → PATH**
  3. Restart your terminal

### ❌ `pip install` fails on `scikit-learn` or `numpy`

- Make sure you have Python 3.12.x (not 3.13+ which may have compatibility issues)
- Try: `pip install --upgrade pip setuptools wheel` then retry

### ❌ `flask db upgrade` shows "Target database is not up to date"

- Run: `flask db stamp head` then `flask db upgrade`

### ❌ MySQL connection refused

- Make sure MySQL service is running:
  1. Press `Win + R`, type `services.msc`, press Enter
  2. Find **MySQL** in the list
  3. Make sure its status is **Running**. If not, right-click → **Start**

### ❌ PowerShell won't activate venv

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### ❌ `ModuleNotFoundError: No module named 'xxx'`

- Make sure your virtual environment is activated (you should see `(.venv)` in your prompt)
- If activated and still failing: `pip install -r requirements.txt`

---

## Daily Workflow (After Setup)

Every time you open a new terminal to work on this project:

```bash
cd %USERPROFILE%\Desktop\Backend\AI_Skill_Gap_Backend_Implementation
.venv\Scripts\activate
flask --app app run --debug
```

---

## Project Structure Overview

```
AI_Skill_Gap_Backend_Implementation/
├── app.py                 ← Flask app factory & CLI commands
├── config.py              ← Configuration (reads from .env)
├── models.py              ← SQLAlchemy database models
├── routes.py              ← Legacy API routes (/api/)
├── auth.py                ← JWT authentication
├── extensions.py          ← Flask extensions (db, migrate)
├── api/                   ← v1 API blueprints (/api/v1/)
│   ├── __init__.py
│   ├── students.py
│   ├── skills.py
│   ├── roles.py
│   ├── gap_analysis.py
│   ├── recommendations.py
│   ├── resumes.py
│   ├── learning.py
│   └── analytics.py
├── services/              ← Business logic layer
│   ├── recommender.py     ← 6-factor recommendation engine
│   ├── gap_engine.py      ← Skill gap analysis
│   ├── resume_parser.py   ← Resume text extraction & NLP
│   ├── skill_normalizer.py← Skill canonicalization
│   └── role_matcher.py    ← Role readiness matching
├── schemas/               ← Marshmallow request validation
├── data/                  ← Data ingestion scripts
├── migrations/            ← Alembic database migrations
├── ml/                    ← ML model training
├── templates/             ← HTML frontend templates
├── static/                ← CSS, JS, images
├── tests/                 ← Pytest test suites
├── requirements.txt       ← Python dependencies
└── .env                   ← Environment config (YOU create this)
```

---

*Setup guide created for the AI Skill Gap Backend project.*
*Last updated: September 2026*
