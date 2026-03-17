"""Seed comprehensive mock data for Scholarr testing."""
import asyncio
import aiohttp
import json
from datetime import date, timedelta
import random

BASE = "http://127.0.0.1:8787/api/v1"
KEY = "test-key-12345"
HEADERS = {"X-API-Key": KEY, "Content-Type": "application/json"}

async def post(session, path, data):
    async with session.post(f"{BASE}{path}", json=data, headers=HEADERS) as r:
        body = await r.json()
        if r.status not in (200, 201):
            print(f"  ERROR {r.status} POST {path}: {body}")
            return None
        return body

async def put(session, path, data):
    async with session.put(f"{BASE}{path}", json=data, headers=HEADERS) as r:
        body = await r.json()
        if r.status not in (200, 201):
            print(f"  ERROR {r.status} PUT {path}: {body}")
        return body

async def get(session, path):
    async with session.get(f"{BASE}{path}", headers=HEADERS) as r:
        return await r.json()

async def main():
    async with aiohttp.ClientSession() as session:

        # ── Semesters ──────────────────────────────────────
        print("\n── Creating Semesters ──────────────────────────────")
        semesters = [
            {"name": "Fall 2024",   "start_date": "2024-09-01", "end_date": "2024-12-20"},
            {"name": "Spring 2025", "start_date": "2025-01-15", "end_date": "2025-05-10"},
            {"name": "Summer 2025", "start_date": "2025-06-01", "end_date": "2025-08-15"},
            {"name": "Fall 2025",   "start_date": "2025-09-02", "end_date": "2025-12-19"},
        ]
        sem_ids = {}
        for s in semesters:
            r = await post(session, "/semesters", s)
            if r:
                sem_ids[s["name"]] = r["id"]
                print(f"  {r['id']:2d} {r['name']:15s} year={r['year']} term={r['term']} courses={r.get('course_count',0)}")

        # Mark Spring 2025 as active
        sp25 = sem_ids.get("Spring 2025")
        if sp25:
            await put(session, f"/semesters/{sp25}", {"active": True, "name": "Spring 2025",
                "start_date": "2025-01-15", "end_date": "2025-05-10"})
            print(f"  Marked Spring 2025 (id={sp25}) as active")

        # ── Courses ────────────────────────────────────────
        print("\n── Creating Courses ────────────────────────────────")
        courses_data = [
            # Fall 2024
            {"name": "Introduction to Computer Science", "code": "CS 101", "professor": "Dr. Reynolds",   "credits": 3, "semester_id": sem_ids["Fall 2024"],   "color": "#2ecfa1"},
            {"name": "Calculus I",                       "code": "MATH 101","professor": "Dr. Okafor",    "credits": 4, "semester_id": sem_ids["Fall 2024"],   "color": "#4e9af1"},
            {"name": "English Composition",              "code": "ENG 110", "professor": "Prof. Martinez","credits": 3, "semester_id": sem_ids["Fall 2024"],   "color": "#f0ad4e"},
            # Spring 2025
            {"name": "Data Structures",                  "code": "CS 201",  "professor": "Dr. Reynolds",  "credits": 3, "semester_id": sem_ids["Spring 2025"], "color": "#2ecfa1"},
            {"name": "Calculus II",                      "code": "MATH 201","professor": "Dr. Okafor",    "credits": 4, "semester_id": sem_ids["Spring 2025"], "color": "#4e9af1"},
            {"name": "Discrete Mathematics",             "code": "CS 205",  "professor": "Dr. Tanaka",    "credits": 3, "semester_id": sem_ids["Spring 2025"], "color": "#9b59b6"},
            # Summer 2025
            {"name": "Web Development Fundamentals",     "code": "CS 230",  "professor": "Dr. Chen",      "credits": 3, "semester_id": sem_ids["Summer 2025"], "color": "#1abc9c"},
            {"name": "Technical Communication",          "code": "ENG 215", "professor": "Prof. Martinez","credits": 2, "semester_id": sem_ids["Summer 2025"], "color": "#f0ad4e"},
            # Fall 2025
            {"name": "Algorithms & Complexity",          "code": "CS 301",  "professor": "Dr. Reynolds",  "credits": 3, "semester_id": sem_ids["Fall 2025"],   "color": "#e74c3c"},
            {"name": "Linear Algebra",                   "code": "MATH 230","professor": "Dr. Okafor",    "credits": 3, "semester_id": sem_ids["Fall 2025"],   "color": "#4e9af1"},
            {"name": "Operating Systems",                "code": "CS 310",  "professor": "Dr. Tanaka",    "credits": 3, "semester_id": sem_ids["Fall 2025"],   "color": "#9b59b6"},
            {"name": "Technical Writing",                "code": "ENG 220", "professor": "Prof. Martinez","credits": 2, "semester_id": sem_ids["Fall 2025"],   "color": "#e67e22"},
        ]
        course_ids = {}
        for c in courses_data:
            r = await post(session, "/courses", c)
            if r:
                course_ids[c["code"]] = r["id"]
                print(f"  {r['id']:2d} {r['code']:10s} {r['name'][:30]:30s} sem={r.get('semester_name','?')[:12]}")

        # ── Academic Items ──────────────────────────────────
        print("\n── Creating Academic Items ─────────────────────────")

        def d(offset_days):
            return (date(2025, 3, 1) + timedelta(days=offset_days)).isoformat()

        items_data = [
            # CS 101 (Fall 2024 — completed)
            {"course_id": course_ids["CS 101"],  "name": "Lab 1 — Hello World",        "type": "Lab",        "status": "Graded",    "grade": 95.0, "due_date": "2024-09-20", "weight": 5},
            {"course_id": course_ids["CS 101"],  "name": "Assignment 1 — Variables",   "type": "Assignment", "status": "Graded",    "grade": 88.0, "due_date": "2024-09-27", "weight": 10},
            {"course_id": course_ids["CS 101"],  "name": "Midterm Exam",               "type": "Exam",       "status": "Graded",    "grade": 82.0, "due_date": "2024-10-15", "weight": 25},
            {"course_id": course_ids["CS 101"],  "name": "Assignment 2 — Functions",   "type": "Assignment", "status": "Graded",    "grade": 91.0, "due_date": "2024-11-01", "weight": 10},
            {"course_id": course_ids["CS 101"],  "name": "Final Project",              "type": "Project",    "status": "Graded",    "grade": 87.0, "due_date": "2024-12-05", "weight": 30},
            {"course_id": course_ids["CS 101"],  "name": "Final Exam",                 "type": "Exam",       "status": "Graded",    "grade": 84.0, "due_date": "2024-12-18", "weight": 20},
            # MATH 101 (Fall 2024 — completed)
            {"course_id": course_ids["MATH 101"],"name": "Quiz 1 — Limits",            "type": "Quiz",       "status": "Graded",    "grade": 78.0, "due_date": "2024-09-25", "weight": 5},
            {"course_id": course_ids["MATH 101"],"name": "Problem Set 1",              "type": "Assignment", "status": "Graded",    "grade": 85.0, "due_date": "2024-10-10", "weight": 15},
            {"course_id": course_ids["MATH 101"],"name": "Midterm",                    "type": "Exam",       "status": "Graded",    "grade": 73.0, "due_date": "2024-10-22", "weight": 30},
            {"course_id": course_ids["MATH 101"],"name": "Problem Set 2",              "type": "Assignment", "status": "Graded",    "grade": 90.0, "due_date": "2024-11-15", "weight": 15},
            {"course_id": course_ids["MATH 101"],"name": "Final Exam",                 "type": "Exam",       "status": "Graded",    "grade": 79.0, "due_date": "2024-12-17", "weight": 35},
            # CS 201 (Spring 2025 — in progress)
            {"course_id": course_ids["CS 201"],  "name": "Lab 1 — Linked Lists",       "type": "Lab",        "status": "Graded",    "grade": 93.0, "due_date": "2025-01-31", "weight": 5},
            {"course_id": course_ids["CS 201"],  "name": "Assignment 1 — Stacks",      "type": "Assignment", "status": "Graded",    "grade": 89.0, "due_date": "2025-02-14", "weight": 10},
            {"course_id": course_ids["CS 201"],  "name": "Midterm Exam",               "type": "Exam",       "status": "Submitted", "grade": None, "due_date": "2025-03-10", "weight": 25},
            {"course_id": course_ids["CS 201"],  "name": "Lab 2 — Binary Trees",       "type": "Lab",        "status": "InProgress","grade": None, "due_date": d(5),         "weight": 5},
            {"course_id": course_ids["CS 201"],  "name": "Assignment 2 — Sorting",     "type": "Assignment", "status": "NotStarted","grade": None, "due_date": d(14),        "weight": 10},
            {"course_id": course_ids["CS 201"],  "name": "Final Project — DSA App",    "type": "Project",    "status": "NotStarted","grade": None, "due_date": d(45),        "weight": 25},
            {"course_id": course_ids["CS 201"],  "name": "Final Exam",                 "type": "Exam",       "status": "NotStarted","grade": None, "due_date": d(55),        "weight": 20},
            # MATH 201 (Spring 2025 — in progress)
            {"course_id": course_ids["MATH 201"],"name": "Problem Set 1 — Integration","type": "Assignment", "status": "Graded",    "grade": 76.0, "due_date": "2025-02-07", "weight": 10},
            {"course_id": course_ids["MATH 201"],"name": "Quiz 1",                     "type": "Quiz",       "status": "Graded",    "grade": 80.0, "due_date": "2025-02-21", "weight": 5},
            {"course_id": course_ids["MATH 201"],"name": "Midterm",                    "type": "Exam",       "status": "Graded",    "grade": 71.0, "due_date": "2025-03-07", "weight": 30},
            {"course_id": course_ids["MATH 201"],"name": "Problem Set 2 — Series",     "type": "Assignment", "status": "InProgress","grade": None, "due_date": d(7),         "weight": 10},
            {"course_id": course_ids["MATH 201"],"name": "Quiz 2",                     "type": "Quiz",       "status": "NotStarted","grade": None, "due_date": d(18),        "weight": 5},
            {"course_id": course_ids["MATH 201"],"name": "Final Exam",                 "type": "Exam",       "status": "NotStarted","grade": None, "due_date": d(58),        "weight": 40},
            # CS 205 (Spring 2025)
            {"course_id": course_ids["CS 205"],  "name": "Problem Set 1 — Logic",      "type": "Assignment", "status": "Graded",    "grade": 94.0, "due_date": "2025-02-03", "weight": 15},
            {"course_id": course_ids["CS 205"],  "name": "Midterm",                    "type": "Exam",       "status": "Graded",    "grade": 88.0, "due_date": "2025-03-05", "weight": 30},
            {"course_id": course_ids["CS 205"],  "name": "Problem Set 2 — Graph Theory","type": "Assignment","status": "InProgress","grade": None, "due_date": d(9),         "weight": 15},
            {"course_id": course_ids["CS 205"],  "name": "Final Exam",                 "type": "Exam",       "status": "NotStarted","grade": None, "due_date": d(52),        "weight": 40},
            # CS 230 (Summer 2025 — upcoming)
            {"course_id": course_ids["CS 230"],  "name": "Project 1 — HTML/CSS Site",  "type": "Project",    "status": "NotStarted","grade": None, "due_date": "2025-06-20", "weight": 20},
            {"course_id": course_ids["CS 230"],  "name": "Midterm — JS Fundamentals",  "type": "Exam",       "status": "NotStarted","grade": None, "due_date": "2025-07-10", "weight": 25},
            {"course_id": course_ids["CS 230"],  "name": "Final Project — Full Stack",  "type": "Project",    "status": "NotStarted","grade": None, "due_date": "2025-08-10", "weight": 40},
            # CS 301 (Fall 2025 — far future)
            {"course_id": course_ids["CS 301"],  "name": "Assignment 1 — Big-O",       "type": "Assignment", "status": "NotStarted","grade": None, "due_date": "2025-09-26", "weight": 10},
            {"course_id": course_ids["CS 301"],  "name": "Midterm",                    "type": "Exam",       "status": "NotStarted","grade": None, "due_date": "2025-10-24", "weight": 30},
            {"course_id": course_ids["CS 301"],  "name": "Final Project — Algorithm",  "type": "Project",    "status": "NotStarted","grade": None, "due_date": "2025-11-28", "weight": 25},
            {"course_id": course_ids["CS 301"],  "name": "Final Exam",                 "type": "Exam",       "status": "NotStarted","grade": None, "due_date": "2025-12-15", "weight": 35},
        ]

        item_count = 0
        for item in items_data:
            r = await post(session, "/academic-items", item)
            if r:
                item_count += 1
        print(f"  Created {item_count} academic items")

        # ── Verify counts ──────────────────────────────────
        print("\n── Verifying Data Consistency ──────────────────────")

        # Semesters with course counts
        sems = await get(session, "/semesters")
        print("\n  Semesters:")
        for s in sems:
            print(f"    {s['id']:2d} {s['name']:15s} courses={s.get('course_count',0)} active={s.get('active',False)}")

        # Courses with semester names and item counts
        courses = await get(session, "/courses")
        print("\n  Courses:")
        for c in courses:
            print(f"    {c['id']:2d} {c['code']:10s} sem={c.get('semester_name','?'):12s} items={c.get('item_count',0)}")

        # Academic items — paginated
        items_resp = await get(session, "/academic-items/paged?page=1&page_size=5")
        print(f"\n  Academic items total: {items_resp.get('total',0)}")
        print(f"  Pages: {items_resp.get('total_pages',0)}")

        # Upcoming deadlines
        upcoming = await get(session, "/academic-items/upcoming?days=14")
        print(f"\n  Upcoming (next 14 days): {len(upcoming)} items")
        for u in upcoming[:5]:
            print(f"    {u['name'][:35]:35s} {u['due_date'][:10]} course_code={u.get('course_code','?')}")

        # History
        hist = await get(session, "/history?page=1&page_size=5")
        print(f"\n  History entries: {hist.get('total', 0)}")

        # Stats endpoint
        stats = await get(session, "/academic-items?status=Graded")
        graded = stats if isinstance(stats, list) else stats.get("items", [])
        print(f"\n  Graded items: {len(graded)}")
        if graded:
            avg = sum(i["grade"] for i in graded if i.get("grade")) / len(graded)
            print(f"  Average grade: {avg:.1f}%")

        # ── Test course_id filter ──────────────────────────
        print("\n── Testing cross-filters ───────────────────────────")
        cs201_id = course_ids.get("CS 201")
        if cs201_id:
            cs201_items = await get(session, f"/academic-items?course_id={cs201_id}")
            items_list = cs201_items if isinstance(cs201_items, list) else cs201_items.get("items", [])
            print(f"  CS 201 items: {len(items_list)}")
            for i in items_list:
                print(f"    {i['name']:35s} {i['status']:12s} grade={i['grade']}")

        # ── Test semester active flag ──────────────────────
        sem_list = await get(session, "/semesters")
        active_sems = [s for s in sem_list if s.get("active")]
        print(f"\n  Active semesters: {[s['name'] for s in active_sems]}")

        # ── Test course update propagates semester_name ───
        if cs201_id:
            updated = await get(session, f"/courses/{cs201_id}")
            print(f"\n  CS 201 detail: semester_name={updated.get('semester_name')} item_count={updated.get('item_count')}")

        print("\n✓ Seed complete")

asyncio.run(main())
