#!/usr/bin/env python3
"""
Interactive manual test script for the AI Skill Gap System.
Uses Python's standard library (urllib.request) - no external packages required!
Runs against the live running server: http://127.0.0.1:5000
"""
import urllib.request
import urllib.error
import json
import time
import sys

BASE_URL = "http://127.0.0.1:5000/api"

def api_call(method, endpoint, payload=None):
    url = f"{BASE_URL}{endpoint}"
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
        print(f"\n[ERROR] Could not connect to server at {BASE_URL}.")
        print("Please ensure the Flask backend is running on port 5000:")
        print("    flask --app app run --port 5000")
        sys.exit(1)

def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def run_manual_test():
    print_header("1. CHECK SERVER HEALTH")
    status, res = api_call("GET", "/health")
    print(f"GET /api/health -> HTTP {status}")
    print(json.dumps(res, indent=2))

    print_header("2. FETCH TARGET ROLES")
    status, roles = api_call("GET", "/roles")
    print(f"Found {len(roles)} available job roles in database:")
    for r in roles:
        print(f"  [{r['id']}] {r['name']} (Source: {r.get('source')})")
    
    # Select target role: Software Developer (or first role)
    target_role = next((r for r in roles if "software developer" in r["name"].lower()), roles[0])
    role_id = target_role["id"]
    print(f"\n--> Selected Target Role: '{target_role['name']}' (ID: {role_id})")

    print_header(f"3. CHECK REQUIRED SKILLS FOR ROLE: {target_role['name']}")
    status, role_skills_res = api_call("GET", f"/roles/{role_id}/skills")
    req_skills = role_skills_res.get("required_skills", [])
    print(f"Required skills ({len(req_skills)} total):")
    for s in req_skills[:6]:
        print(f"  - Skill: {s['skill']:<25} Required Level: {s['required_level']}/100  Relation: {s['relation_type']}")
    if len(req_skills) > 6:
        print(f"  ... and {len(req_skills) - 6} more")

    print_header("4. REGISTER A NEW STUDENT")
    timestamp = int(time.time())
    student_payload = {
        "name": f"Alex Student {timestamp % 1000}",
        "email": f"alex_{timestamp}@example.edu",
        "course": "MCA",
        "year": 2,
        "target_career": target_role["name"]
    }
    status, student = api_call("POST", "/students", student_payload)
    student_id = student["id"]
    print(f"Registered Student: {student['name']} (ID: {student_id})")

    print_header("5. ADD INITIAL STUDENT SKILLS (Current Evidence)")
    skills_to_add = []
    if len(req_skills) >= 3:
        skills_to_add = [
            {"skill_id": req_skills[0]["skill_id"], "skill_name": req_skills[0]["skill"], "level": 70.0},
            {"skill_id": req_skills[1]["skill_id"], "skill_name": req_skills[1]["skill"], "level": 40.0},
            {"skill_id": req_skills[2]["skill_id"], "skill_name": req_skills[2]["skill"], "level": 20.0},
        ]
    else:
        skills_to_add = [{"skill_id": 1, "skill_name": "Core Skill", "level": 50.0}]

    for item in skills_to_add:
        payload = {"skill_id": item["skill_id"], "proficiency": item["level"], "evidence_type": "self_reported"}
        status, _ = api_call("POST", f"/students/{student_id}/skills", payload)
        print(f"  + Added Skill: {item['skill_name']:<25} Current Level: {item['level']}/100")

    print_header("6. RUN ML SKILL GAP ANALYSIS")
    gap_payload = {"student_id": student_id, "job_role_id": role_id}
    status, gap_data = api_call("POST", "/skill-gap/analyze", gap_payload)
    gaps = gap_data.get("gaps", [])
    print(f"Role: {gap_data.get('job_role')} | Model: {gaps[0].get('model_version') if gaps else 'N/A'}")
    print(f"\n{'Skill':<25} {'Current':<9} {'Required':<10} {'Gap':<8} {'Severity':<9} {'Priority':<8}")
    print("-" * 75)
    for g in gaps:
        print(f"{g['skill']:<25} {g['current_level']:<9.1f} {g['required_level']:<10.1f} {g['gap']:<8.1f} {g['severity']:<9} {g['priority_score']:<8.1f}")

    print_header("7. GENERATE PERSONALIZED COURSE RECOMMENDATIONS")
    status, recs = api_call("GET", f"/students/{student_id}/recommendations?top_k=3")
    print(f"Top {len(recs)} Recommendations Ranked by AI Recommender Engine:")
    for idx, r in enumerate(recs, 1):
        print(f"\n  #{idx} Course: {r['title']}")
        print(f"     Provider: {r.get('provider')} | Match Score: {r['score']} | Target Skill: {r['skill']}")
        print(f"     Why: {r['reason']}")
        print(f"     URL: {r.get('url')}")

    if recs:
        rec_to_enroll = recs[0]
        print_header("8. RECORD LEARNING PROGRESS (Enroll & Complete 50%)")
        prog_payload = {
            "title": rec_to_enroll["title"],
            "course_id": rec_to_enroll.get("course_id"),
            "skill_id": rec_to_enroll.get("skill_id"),
            "status": "in_progress",
            "completion": 50.0
        }
        status, prog_res = api_call("POST", f"/students/{student_id}/progress", prog_payload)
        print("Enrolled in course:")
        print(json.dumps(prog_res, indent=2))

    print_header("9. SUBMIT REASSESSMENT (Skill Level Improvement)")
    reassess_skill = skills_to_add[0]
    print(f"Reassessing skill: {reassess_skill['skill_name']} from {reassess_skill['level']} -> 90.0")
    reassess_payload = {
        "skill_id": reassess_skill["skill_id"],
        "new_level": 90.0,
        "job_role_id": role_id
    }
    status, reassess_data = api_call("POST", f"/students/{student_id}/reassessment", reassess_payload)
    print(f"Improvement recorded: +{reassess_data.get('improvement')} points!")
    print(f"Old Level: {reassess_data.get('old_level')}  -->  New Level: {reassess_data.get('new_level')}")

    print_header("10. STUDENT DASHBOARD SUMMARY")
    status, dash = api_call("GET", f"/students/{student_id}/dashboard")
    print(f"Student: {dash['student']['name']} | Career Goal: {dash['student']['target_career']}")
    print(f"Current Skills Count: {len(dash['current_skills'])}")
    print(f"Top Priority Gaps: {len(dash['top_gaps'])}")
    print("Top Active Learning Path:")
    for p in dash.get("active_learning_path", []):
        print(f"  - {p['title']}: {p['completion']}% ({p['status']})")
    print(f"\nProgress Summary: {dash['progress_summary']}")

    print_header("ALL 10 TEST STEPS COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    run_manual_test()
