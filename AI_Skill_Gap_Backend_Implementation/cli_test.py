#!/usr/bin/env python3
"""
cli_test.py — Interactive Terminal CLI for testing the AI Skill Gap System manually.

Run directly in terminal:
    python cli_test.py
or:
    .venv/bin/python cli_test.py
"""
import sys
import json
import urllib.request
import urllib.error

# Connect either via live server HTTP or internal test_client fallback
LIVE_SERVER_URL = "http://127.0.0.1:5000/api"
_use_test_client = False
_client = None

def init_client():
    global _use_test_client, _client
    try:
        req = urllib.request.Request(f"{LIVE_SERVER_URL}/health")
        with urllib.request.urlopen(req, timeout=1) as resp:
            if resp.status == 200:
                print(f"[Mode] Connected to live Flask server at {LIVE_SERVER_URL}\n")
                return
    except Exception:
        pass

    # Fallback to in-process Flask test client
    try:
        from app import create_app
        app = create_app()
        _client = app.test_client()
        _use_test_client = True
        print("[Mode] Flask server not running on port 5000.")
        print("[Mode] Using internal database test-client (standalone offline mode).\n")
    except Exception as e:
        print(f"[ERROR] Could not initialize backend: {e}")
        sys.exit(1)

def api_call(method, endpoint, payload=None):
    if not _use_test_client:
        url = f"{LIVE_SERVER_URL}{endpoint}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"} if payload is not None else {}
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                body = resp.read().decode("utf-8")
                return resp.status, json.loads(body) if body else {}
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            return e.code, json.loads(body) if body else {}
        except urllib.error.URLError as e:
            print(f"[Error] Failed to connect: {e}")
            return 500, {}
    else:
        url = f"/api{endpoint}"
        if method == "GET":
            resp = _client.get(url)
        elif method == "POST":
            resp = _client.post(url, json=payload)
        elif method == "PUT":
            resp = _client.put(url, json=payload)
        else:
            raise ValueError(f"Unsupported method {method}")
        data = resp.get_json() if resp.is_json else {}
        return resp.status_code, data

def ask_input(prompt, default=""):
    suffix = f" [{default}]" if default else ""
    try:
        val = input(f"{prompt}{suffix}: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting...")
        sys.exit(0)
    return val if val else default

def print_banner(text):
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)

def step_by_step_wizard():
    print_banner("STEP 1: ENTER STUDENT DETAILS")
    name = ask_input("Enter Student Full Name", "Rahul Sharma")
    email_default = name.lower().replace(" ", ".") + "@example.com"
    email = ask_input("Enter Email Address", email_default)
    course = ask_input("Enter Current Degree/Course", "MCA")
    year = int(ask_input("Enter Academic Year (1-4)", "2"))

    print_banner("STEP 2: CHOOSE TARGET CAREER ROLE")
    status, roles = api_call("GET", "/roles")
    if not roles:
        print("[Error] No job roles found in database. Did you run 'flask ingest-data'?")
        return

    for idx, r in enumerate(roles, 1):
        print(f"  [{idx}] {r['name']}")
    
    role_choice = ask_input(f"Select Role (1-{len(roles)})", "1")
    try:
        role_idx = int(role_choice) - 1
        selected_role = roles[role_idx]
    except Exception:
        selected_role = roles[0]
    
    role_id = selected_role["id"]
    role_name = selected_role["name"]
    print(f"\n--> Selected Role: {role_name} (ID: {role_id})")

    # Register student
    student_payload = {
        "name": name,
        "email": email,
        "course": course,
        "year": year,
        "target_career": role_name
    }
    status, student = api_call("POST", "/students", student_payload)
    if status not in (200, 201):
        print(f"[Notice] {student.get('error', 'Using student')}")
        student_id = 1
    else:
        student_id = student["id"]
        print(f"[OK] Registered Student Profile (ID: {student_id})")

    # Fetch required skills for role
    print_banner(f"STEP 3: ENTER YOUR CURRENT SKILLS FOR: {role_name}")
    status, role_skills_res = api_call("GET", f"/roles/{role_id}/skills")
    req_skills = role_skills_res.get("required_skills", [])
    
    print("Here are key skills required for this job role.")
    print("Enter your current proficiency (1 to 100) for each:\n")

    skills_to_prompt = req_skills[:6] if len(req_skills) >= 6 else req_skills
    for s in skills_to_prompt:
        skill_id = s["skill_id"]
        skill_name = s["skill"]
        req_lvl = s["required_level"]
        
        prof_str = ask_input(f"  {skill_name:<28} (Job requires: {req_lvl}/100) Your Level (1-100)", "40")
        try:
            prof = float(prof_str)
        except ValueError:
            prof = 40.0
            
        payload = {
            "skill_id": skill_id,
            "proficiency": prof,
            "evidence_type": "self_reported"
        }
        api_call("POST", f"/students/{student_id}/skills", payload)

    print_banner("STEP 4: RUNNING AI SKILL GAP ANALYSIS")
    gap_payload = {"student_id": student_id, "job_role_id": role_id}
    status, gap_res = api_call("POST", "/skill-gap/analyze", gap_payload)
    
    gaps = gap_res.get("gaps", [])
    if not gaps:
        print("No gaps detected or error running gap engine.")
        print(gap_res)
        return

    print(f"Role: {gap_res.get('job_role')} | Total Evaluated Skills: {len(gaps)}")
    print(f"\n{'Skill':<28} {'Current':<9} {'Required':<10} {'Gap':<8} {'Severity':<9} {'Priority':<8}")
    print("-" * 75)
    for g in gaps:
        sev = g['severity']
        color = "\033[91m" if sev == "HIGH" else ("\033[93m" if sev == "MEDIUM" else "\033[92m")
        reset = "\033[0m"
        print(f"{g['skill']:<28} {g['current_level']:<9.1f} {g['required_level']:<10.1f} {g['gap']:<8.1f} {color}{sev:<9}{reset} {g['priority_score']:<8.1f}")

    print_banner("STEP 5: AI COURSE RECOMMENDATIONS")
    k_str = ask_input("How many top course recommendations to view?", "4")
    try:
        top_k = int(k_str)
    except ValueError:
        top_k = 4

    status, recs = api_call("GET", f"/students/{student_id}/recommendations?top_k={top_k}")
    if not recs or not isinstance(recs, list):
        print("No recommendations returned.")
        return

    for idx, r in enumerate(recs, 1):
        print(f"\n  #{idx} Course: \033[1m{r['title']}\033[0m")
        print(f"     Target Skill : {r.get('skill')}")
        print(f"     Match Score  : {r.get('score')} | Provider: {r.get('provider')}")
        print(f"     Why Ranked   : {r.get('reason')}")
        if r.get("url"):
            print(f"     Course Link  : {r.get('url')}")

    print_banner("TEST RUN COMPLETED SUCCESSFULLY!")
    print(f"Student ID {student_id} is saved in the database.")
    print("You can view their full dashboard via: GET /api/students/<id>/dashboard\n")

def test_resume_parser_interactive():
    print_banner("TEST RESUME PARSER")
    path = ask_input("Enter path to a PDF or DOCX resume file")
    if not path:
        print("No path entered.")
        return
    import os
    if not os.path.exists(path):
        print(f"[Error] File not found: {path}")
        return

    try:
        from services.resume_parser import extract_text, normalize_text, candidate_skills, extract_projects_text, extract_certifications_text
        from models import Skill
        from app import create_app
        app = create_app()
        with app.app_context():
            skills_vocab = [s.name for s in Skill.query.all()]
            raw = extract_text(path)
            norm = normalize_text(raw)
            extracted = candidate_skills(norm, skills_vocab)
            projects = extract_projects_text(norm)
            certs = extract_certifications_text(norm)
            
            print(f"\nExtracted {len(extracted)} Skills from Resume:")
            for s in extracted:
                print(f"  • {s['skill']:<25} (Confidence: {s['confidence_score']:.2f}, Source: {s['source_section']})")
            
            if projects:
                print(f"\nProjects section detected: {len(projects)} chars")
            if certs:
                print(f"Certifications section detected: {len(certs)} chars")
    except Exception as e:
        print(f"[Error] Failed to parse: {e}")

def main_menu():
    init_client()
    while True:
        print("=" * 60)
        print("   AI SKILL GAP SYSTEM — MANUAL TERMINAL TEST")
        print("=" * 60)
        print("  [1] Interactive Step-by-Step Test Wizard (Recommended)")
        print("  [2] View All Available Job Roles & Requirements")
        print("  [3] Test Resume Parser with a PDF/DOCX file")
        print("  [4] View Server Health & Status")
        print("  [0] Exit")
        print("=" * 60)
        
        choice = ask_input("Enter your choice (0-4)", "1")
        if choice == "1":
            step_by_step_wizard()
        elif choice == "2":
            status, roles = api_call("GET", "/roles")
            print("\nAvailable Job Roles:")
            for r in roles:
                print(f"  • ID {r['id']}: {r['name']}")
            r_id = ask_input("\nEnter Role ID to see required skills (or Enter to skip)")
            if r_id:
                status, res = api_call("GET", f"/roles/{r_id}/skills")
                reqs = res.get("required_skills", [])
                print(f"\nRequired Skills for Role ({len(reqs)} total):")
                for s in reqs[:15]:
                    print(f"  - {s['skill']:<25} Required Level: {s['required_level']}/100 ({s['relation_type']})")
                if len(reqs) > 15:
                    print(f"  ... and {len(reqs) - 15} more")
            print()
        elif choice == "3":
            test_resume_parser_interactive()
        elif choice == "4":
            status, res = api_call("GET", "/health")
            print(f"\nHealth Check Response (HTTP {status}):")
            print(json.dumps(res, indent=2), "\n")
        elif choice == "0":
            print("\nGoodbye!")
            break
        else:
            print("Invalid choice, please try again.\n")

if __name__ == "__main__":
    main_menu()
