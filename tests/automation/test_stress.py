"""Intensive stress tests for the Scholarr API.

Tests cover: rapid CRUD cycles, edge cases, boundary values, concurrent-style
operations, cascade integrity, pagination limits, search/filter combos,
special characters, and bulk operations.
"""

from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _h(api_key: str) -> dict:
    """Shortcut for auth headers."""
    return {"X-API-Key": api_key}


async def _create_semester(client: AsyncClient, api_key: str, suffix: str = "") -> dict:
    """Create a semester via API and return the response dict."""
    r = await client.post(
        "/api/v1/semesters",
        json={
            "name": f"Fall 2025{suffix}",
            "year": 2025,
            "term": "Fall",
            "start_date": "2025-09-01T00:00:00",
            "end_date": "2025-12-15T00:00:00",
            "active": False,
        },
        headers=_h(api_key),
    )
    assert r.status_code in (200, 201), f"Semester create failed: {r.status_code} {r.text}"
    return r.json()


async def _create_course(
    client: AsyncClient, api_key: str, semester_id: int, code: str = "CS101", name: str = "Intro to CS"
) -> dict:
    r = await client.post(
        "/api/v1/courses",
        json={
            "code": code,
            "name": name,
            "semester_id": semester_id,
            "credits": 3.0,
            "monitored": True,
        },
        headers=_h(api_key),
    )
    assert r.status_code in (200, 201), f"Course create failed: {r.status_code} {r.text}"
    return r.json()


async def _create_item(
    client: AsyncClient,
    api_key: str,
    course_id: int,
    item_type: str = "Assignment",
    name: str = "HW 1",
    **extra,
) -> dict:
    payload = {
        "course_id": course_id,
        "type": item_type,
        "name": name,
        "status": "NotStarted",
        **extra,
    }
    r = await client.post("/api/v1/academic-items", json=payload, headers=_h(api_key))
    assert r.status_code in (200, 201), f"Item create failed: {r.status_code} {r.text}"
    return r.json()


async def _create_note(
    client: AsyncClient, api_key: str, title: str = "Note", course_id: int | None = None, **extra
) -> dict:
    payload: dict = {"title": title, **extra}
    if course_id is not None:
        payload["course_id"] = course_id
    r = await client.post("/api/v1/notes", json=payload, headers=_h(api_key))
    assert r.status_code in (200, 201), f"Note create failed: {r.status_code} {r.text}"
    return r.json()


# ===========================================================================
# SEMESTER STRESS TESTS
# ===========================================================================


class TestSemesterStress:
    """Stress tests for the semester API."""

    async def test_create_many_semesters(self, test_client, api_key):
        """Create semesters for every term across many years."""
        terms = ["Winter", "Spring", "Summer", "Fall"]
        created = 0
        for year in range(2020, 2030):
            for term in terms:
                r = await test_client.post(
                    "/api/v1/semesters",
                    json={
                        "name": f"{term} {year}",
                        "year": year,
                        "term": term,
                        "start_date": f"{year}-01-01T00:00:00",
                        "end_date": f"{year}-06-01T00:00:00",
                    },
                    headers=_h(api_key),
                )
                assert r.status_code in (200, 201)
                created += 1

        # Verify all were created
        r = await test_client.get("/api/v1/semesters", headers=_h(api_key))
        assert r.status_code == 200
        assert len(r.json()) >= created

    async def test_activate_deactivate_cycle(self, test_client, api_key):
        """Rapidly toggle active semester."""
        ids = []
        for i in range(5):
            r = await test_client.post(
                "/api/v1/semesters",
                json={
                    "name": f"Toggle {i}",
                    "year": 2040 + i,
                    "term": "Fall",
                    "start_date": f"{2040 + i}-09-01T00:00:00",
                    "end_date": f"{2040 + i}-12-15T00:00:00",
                },
                headers=_h(api_key),
            )
            assert r.status_code in (200, 201)
            ids.append(r.json()["id"])

        # Toggle active through all
        for sid in ids * 3:  # 15 toggles
            r = await test_client.put(
                f"/api/v1/semesters/{sid}/activate",
                headers=_h(api_key),
            )
            assert r.status_code == 200

    async def test_duplicate_semester_rejected(self, test_client, api_key):
        """Cannot create two semesters with same year+term."""
        payload = {
            "name": "DupTest",
            "year": 2099,
            "term": "Spring",
            "start_date": "2099-01-01T00:00:00",
            "end_date": "2099-06-01T00:00:00",
        }
        r1 = await test_client.post("/api/v1/semesters", json=payload, headers=_h(api_key))
        assert r1.status_code in (200, 201)

        r2 = await test_client.post("/api/v1/semesters", json=payload, headers=_h(api_key))
        assert r2.status_code in (400, 409, 422)

    async def test_end_before_start_rejected(self, test_client, api_key):
        """End date before start date should be rejected."""
        r = await test_client.post(
            "/api/v1/semesters",
            json={
                "name": "Backwards",
                "year": 2098,
                "term": "Fall",
                "start_date": "2098-12-15T00:00:00",
                "end_date": "2098-09-01T00:00:00",
            },
            headers=_h(api_key),
        )
        assert r.status_code == 422


# ===========================================================================
# COURSE STRESS TESTS
# ===========================================================================


class TestCourseStress:
    """Stress tests for the course API."""

    @pytest_asyncio.fixture
    async def semester(self, test_client, api_key):
        return await _create_semester(test_client, api_key)

    async def test_create_50_courses(self, test_client, api_key, semester):
        """Create 50 courses in one semester."""
        for i in range(50):
            code = f"CS{100 + i:03d}"
            r = await test_client.post(
                "/api/v1/courses",
                json={
                    "code": code,
                    "name": f"Course {i}",
                    "semester_id": semester["id"],
                    "credits": round(1.0 + (i % 5), 1),
                },
                headers=_h(api_key),
            )
            assert r.status_code in (200, 201), f"Failed creating course {code}: {r.text}"

        # Verify count
        r = await test_client.get(
            f"/api/v1/courses?semester_id={semester['id']}", headers=_h(api_key)
        )
        assert r.status_code == 200
        assert len(r.json()) == 50

    async def test_duplicate_code_same_semester_rejected(self, test_client, api_key, semester):
        """Two courses with the same code in the same semester should fail."""
        course_data = {
            "code": "DUP100",
            "name": "Original",
            "semester_id": semester["id"],
        }
        r1 = await test_client.post("/api/v1/courses", json=course_data, headers=_h(api_key))
        assert r1.status_code in (200, 201)

        r2 = await test_client.post(
            "/api/v1/courses",
            json={**course_data, "name": "Duplicate"},
            headers=_h(api_key),
        )
        assert r2.status_code in (400, 409, 422)

    async def test_pagination_edge_cases(self, test_client, api_key, semester):
        """Test pagination with various edge cases."""
        # Create 15 courses
        for i in range(15):
            await _create_course(test_client, api_key, semester["id"], f"PG{i:03d}", f"Page Course {i}")

        # Page 1, size 5
        r = await test_client.get(
            f"/api/v1/courses/paged?page=1&page_size=5&semester_id={semester['id']}",
            headers=_h(api_key),
        )
        assert r.status_code == 200
        data = r.json()
        assert len(data["items"]) == 5
        assert data["total"] == 15
        assert data["total_pages"] == 3

        # Last page
        r = await test_client.get(
            f"/api/v1/courses/paged?page=3&page_size=5&semester_id={semester['id']}",
            headers=_h(api_key),
        )
        assert r.status_code == 200
        assert len(r.json()["items"]) == 5

        # Beyond last page
        r = await test_client.get(
            f"/api/v1/courses/paged?page=100&page_size=5&semester_id={semester['id']}",
            headers=_h(api_key),
        )
        assert r.status_code == 200
        assert len(r.json()["items"]) == 0

        # Page size 1
        r = await test_client.get(
            f"/api/v1/courses/paged?page=1&page_size=1&semester_id={semester['id']}",
            headers=_h(api_key),
        )
        assert r.status_code == 200
        assert len(r.json()["items"]) == 1
        assert r.json()["total_pages"] == 15

    async def test_search_special_characters(self, test_client, api_key, semester):
        """Search with special characters shouldn't crash."""
        await _create_course(test_client, api_key, semester["id"], "SPEC01", "C++ Programming & Design")

        for query in ["C++", "Programming & Design", "C%2B%2B", "a'b", 'a"b', "a<b>c"]:
            r = await test_client.get(
                f"/api/v1/courses?search={query}",
                headers=_h(api_key),
            )
            assert r.status_code == 200  # Should not 500

    async def test_update_nonexistent_course(self, test_client, api_key):
        """Updating a non-existent course returns 404."""
        r = await test_client.put(
            "/api/v1/courses/99999",
            json={"name": "Ghost"},
            headers=_h(api_key),
        )
        assert r.status_code == 404

    async def test_delete_nonexistent_course(self, test_client, api_key):
        """Deleting a non-existent course returns 404."""
        r = await test_client.delete("/api/v1/courses/99999", headers=_h(api_key))
        assert r.status_code == 404

    async def test_rapid_create_update_delete(self, test_client, api_key, semester):
        """Rapidly create, update, then delete a course."""
        for i in range(20):
            # Create
            c = await _create_course(test_client, api_key, semester["id"], f"RAP{i:03d}", f"Rapid {i}")
            cid = c["id"]

            # Update
            r = await test_client.put(
                f"/api/v1/courses/{cid}",
                json={"name": f"Updated Rapid {i}", "credits": 4.0},
                headers=_h(api_key),
            )
            assert r.status_code == 200

            # Delete
            r = await test_client.delete(f"/api/v1/courses/{cid}", headers=_h(api_key))
            assert r.status_code in (200, 204)

            # Verify gone
            r = await test_client.get(f"/api/v1/courses/{cid}", headers=_h(api_key))
            assert r.status_code == 404

    async def test_course_with_max_length_fields(self, test_client, api_key, semester):
        """Create course with maximum length field values."""
        r = await test_client.post(
            "/api/v1/courses",
            json={
                "code": "X" * 50,
                "name": "A" * 255,
                "professor": "P" * 255,
                "semester_id": semester["id"],
                "section": "S" * 50,
                "credits": 20.0,
                "notes": "N" * 5000,
            },
            headers=_h(api_key),
        )
        assert r.status_code in (200, 201)

    async def test_course_empty_code_rejected(self, test_client, api_key, semester):
        """Course with empty code should be rejected."""
        r = await test_client.post(
            "/api/v1/courses",
            json={"code": "", "name": "No Code", "semester_id": semester["id"]},
            headers=_h(api_key),
        )
        assert r.status_code == 422

    async def test_course_missing_name_rejected(self, test_client, api_key, semester):
        """Course without name should be rejected."""
        r = await test_client.post(
            "/api/v1/courses",
            json={"code": "NONAME", "semester_id": semester["id"]},
            headers=_h(api_key),
        )
        assert r.status_code == 422


# ===========================================================================
# ACADEMIC ITEM STRESS TESTS
# ===========================================================================


class TestAcademicItemStress:
    """Stress tests for academic items."""

    @pytest_asyncio.fixture
    async def setup(self, test_client, api_key):
        sem = await _create_semester(test_client, api_key)
        course = await _create_course(test_client, api_key, sem["id"])
        return {"semester": sem, "course": course}

    async def test_create_100_items(self, test_client, api_key, setup):
        """Create 100 academic items for one course."""
        cid = setup["course"]["id"]
        types = ["Assignment", "Lab", "Exam", "Quiz", "Project", "Notes", "Slides"]

        for i in range(100):
            item_type = types[i % len(types)]
            r = await test_client.post(
                "/api/v1/academic-items",
                json={
                    "course_id": cid,
                    "type": item_type,
                    "name": f"{item_type} {i}",
                    "number": str(i),
                    "status": "NotStarted",
                    "weight": round((i % 10) + 0.5, 1),
                },
                headers=_h(api_key),
            )
            assert r.status_code in (200, 201), f"Failed at item {i}: {r.text}"

        # Verify count
        r = await test_client.get(
            f"/api/v1/academic-items?course_id={cid}", headers=_h(api_key)
        )
        assert r.status_code == 200
        assert len(r.json()) == 100

    async def test_all_status_transitions(self, test_client, api_key, setup):
        """Cycle through all valid status values."""
        cid = setup["course"]["id"]
        item = await _create_item(test_client, api_key, cid)
        iid = item["id"]

        statuses = ["NotStarted", "InProgress", "Submitted", "Graded", "Late", "Incomplete", "Complete"]
        for status in statuses:
            r = await test_client.put(
                f"/api/v1/academic-items/{iid}",
                json={"status": status},
                headers=_h(api_key),
            )
            assert r.status_code == 200, f"Status {status} failed: {r.text}"
            assert r.json()["status"] == status

    async def test_all_item_types(self, test_client, api_key, setup):
        """Create items with every valid type."""
        cid = setup["course"]["id"]
        types = [
            "Assignment", "Lab", "Lecture", "Exam", "Paper", "Project",
            "Notes", "Syllabus", "Textbook", "Slides", "Tutorial", "Quiz", "Other",
        ]
        for t in types:
            r = await test_client.post(
                "/api/v1/academic-items",
                json={"course_id": cid, "type": t, "name": f"Type {t}"},
                headers=_h(api_key),
            )
            assert r.status_code in (200, 201), f"Type {t} failed: {r.text}"

    async def test_grade_boundary_values(self, test_client, api_key, setup):
        """Test grade values at boundaries."""
        cid = setup["course"]["id"]

        # Grade = 0
        item = await _create_item(test_client, api_key, cid, name="Zero Grade")
        r = await test_client.put(
            f"/api/v1/academic-items/{item['id']}",
            json={"grade": 0.0},
            headers=_h(api_key),
        )
        assert r.status_code == 200
        assert r.json()["grade"] == 0.0

        # Grade = 100
        item2 = await _create_item(test_client, api_key, cid, name="Perfect Grade")
        r = await test_client.put(
            f"/api/v1/academic-items/{item2['id']}",
            json={"grade": 100.0},
            headers=_h(api_key),
        )
        assert r.status_code == 200
        assert r.json()["grade"] == 100.0

        # Bonus grade > 100 (allowed per schema)
        item3 = await _create_item(test_client, api_key, cid, name="Bonus Grade")
        r = await test_client.put(
            f"/api/v1/academic-items/{item3['id']}",
            json={"grade": 105.0},
            headers=_h(api_key),
        )
        assert r.status_code == 200

        # Negative grade should be rejected
        item4 = await _create_item(test_client, api_key, cid, name="Neg Grade")
        r = await test_client.put(
            f"/api/v1/academic-items/{item4['id']}",
            json={"grade": -1.0},
            headers=_h(api_key),
        )
        assert r.status_code == 422

    async def test_weight_boundary_values(self, test_client, api_key, setup):
        """Test weight values at boundaries."""
        cid = setup["course"]["id"]

        # Weight = 0
        r = await test_client.post(
            "/api/v1/academic-items",
            json={"course_id": cid, "type": "Assignment", "name": "W0", "weight": 0.0},
            headers=_h(api_key),
        )
        assert r.status_code in (200, 201)

        # Weight = 100
        r = await test_client.post(
            "/api/v1/academic-items",
            json={"course_id": cid, "type": "Assignment", "name": "W100", "weight": 100.0},
            headers=_h(api_key),
        )
        assert r.status_code in (200, 201)

        # Weight > 100 should be rejected
        r = await test_client.post(
            "/api/v1/academic-items",
            json={"course_id": cid, "type": "Assignment", "name": "W101", "weight": 101.0},
            headers=_h(api_key),
        )
        assert r.status_code == 422

        # Weight < 0 should be rejected
        r = await test_client.post(
            "/api/v1/academic-items",
            json={"course_id": cid, "type": "Assignment", "name": "Wneg", "weight": -1.0},
            headers=_h(api_key),
        )
        assert r.status_code == 422

    async def test_invalid_type_rejected(self, test_client, api_key, setup):
        """Invalid item type should be rejected."""
        cid = setup["course"]["id"]
        r = await test_client.post(
            "/api/v1/academic-items",
            json={"course_id": cid, "type": "NonExistentType", "name": "Bad"},
            headers=_h(api_key),
        )
        assert r.status_code == 422

    async def test_filter_combinations(self, test_client, api_key, setup):
        """Test combining multiple filters."""
        cid = setup["course"]["id"]
        # Create items with different statuses and types
        await _create_item(test_client, api_key, cid, "Assignment", "A1")
        await _create_item(test_client, api_key, cid, "Exam", "E1")
        item = await _create_item(test_client, api_key, cid, "Assignment", "A2")
        await test_client.put(
            f"/api/v1/academic-items/{item['id']}",
            json={"status": "InProgress"},
            headers=_h(api_key),
        )

        # Filter by type
        r = await test_client.get(
            f"/api/v1/academic-items?course_id={cid}&type=Assignment",
            headers=_h(api_key),
        )
        assert r.status_code == 200
        items = r.json()
        assert all(i["type"] == "Assignment" for i in items)

        # Filter by status
        r = await test_client.get(
            f"/api/v1/academic-items?course_id={cid}&status=InProgress",
            headers=_h(api_key),
        )
        assert r.status_code == 200

    async def test_upcoming_deadlines(self, test_client, api_key, setup):
        """Test upcoming deadlines with various day ranges."""
        cid = setup["course"]["id"]
        now = datetime.now(UTC)

        # Due tomorrow
        await _create_item(
            test_client, api_key, cid, name="Due Tomorrow",
            due_date=(now + timedelta(days=1)).isoformat(),
        )
        # Due in 14 days
        await _create_item(
            test_client, api_key, cid, name="Due in 2 weeks",
            due_date=(now + timedelta(days=14)).isoformat(),
        )
        # Due in 60 days
        await _create_item(
            test_client, api_key, cid, name="Due in 2 months",
            due_date=(now + timedelta(days=60)).isoformat(),
        )

        # Within 7 days
        r = await test_client.get(
            "/api/v1/academic-items/upcoming?days=7",
            headers=_h(api_key),
        )
        assert r.status_code == 200
        names = [i["name"] for i in r.json()]
        assert "Due Tomorrow" in names
        assert "Due in 2 months" not in names

    async def test_item_with_no_course(self, test_client, api_key):
        """Create item with course_id=0 (treated as None) or invalid course."""
        r = await test_client.post(
            "/api/v1/academic-items",
            json={"course_id": 0, "type": "Other", "name": "Orphan"},
            headers=_h(api_key),
        )
        # The app requires at least one course to exist, so 422 is expected
        assert r.status_code in (200, 201, 400, 422)


# ===========================================================================
# CASCADE DELETE TESTS
# ===========================================================================


class TestCascadeIntegrity:
    """Test that cascade deletes and referential integrity hold up."""

    async def test_delete_semester_cascades_to_courses(self, test_client, api_key):
        """Deleting a semester should delete its courses."""
        sem = await _create_semester(test_client, api_key)
        sid = sem["id"]

        # Create courses
        course_ids = []
        for i in range(5):
            c = await _create_course(test_client, api_key, sid, f"CASC{i:02d}", f"Cascade {i}")
            course_ids.append(c["id"])

        # Delete semester
        r = await test_client.delete(f"/api/v1/semesters/{sid}", headers=_h(api_key))
        assert r.status_code in (200, 204)

        # All courses should be gone
        for cid in course_ids:
            r = await test_client.get(f"/api/v1/courses/{cid}", headers=_h(api_key))
            assert r.status_code == 404

    async def test_delete_course_cascades_to_items(self, test_client, api_key):
        """Deleting a course should delete its academic items."""
        sem = await _create_semester(test_client, api_key)
        course = await _create_course(test_client, api_key, sem["id"], "CDEL01", "Cascade Delete")
        cid = course["id"]

        item_ids = []
        for i in range(10):
            item = await _create_item(test_client, api_key, cid, name=f"Item {i}")
            item_ids.append(item["id"])

        # Delete course
        r = await test_client.delete(f"/api/v1/courses/{cid}", headers=_h(api_key))
        assert r.status_code in (200, 204)

        # All items should be gone
        for iid in item_ids:
            r = await test_client.get(f"/api/v1/academic-items/{iid}", headers=_h(api_key))
            assert r.status_code == 404

    async def test_deep_cascade_semester_to_items(self, test_client, api_key):
        """Semester delete cascades through courses to items."""
        sem = await _create_semester(test_client, api_key)
        course = await _create_course(test_client, api_key, sem["id"], "DEEP01", "Deep")
        item = await _create_item(test_client, api_key, course["id"], name="Deep Item")

        # Delete semester
        r = await test_client.delete(f"/api/v1/semesters/{sem['id']}", headers=_h(api_key))
        assert r.status_code in (200, 204)

        # Item should be gone
        r = await test_client.get(f"/api/v1/academic-items/{item['id']}", headers=_h(api_key))
        assert r.status_code == 404


# ===========================================================================
# NOTE STRESS TESTS
# ===========================================================================


class TestNoteStress:
    """Stress tests for the notes API."""

    async def test_create_many_notes(self, test_client, api_key):
        """Create 50 notes rapidly."""
        for i in range(50):
            r = await test_client.post(
                "/api/v1/notes",
                json={"title": f"Note {i}", "content": f"Content for note {i}"},
                headers=_h(api_key),
            )
            assert r.status_code in (200, 201)

        r = await test_client.get("/api/v1/notes", headers=_h(api_key))
        assert r.status_code == 200
        data = r.json()
        # Notes endpoint may return paginated or raw list
        items = data["items"] if isinstance(data, dict) and "items" in data else data
        assert len(items) >= 50

    async def test_note_large_content(self, test_client, api_key):
        """Note with very large content body."""
        large_content = "x" * 100_000  # 100KB of text
        r = await test_client.post(
            "/api/v1/notes",
            json={"title": "Large Note", "content": large_content},
            headers=_h(api_key),
        )
        assert r.status_code in (200, 201)
        note_id = r.json()["id"]

        # Verify content preserved
        r = await test_client.get(f"/api/v1/notes/{note_id}", headers=_h(api_key))
        assert r.status_code == 200
        assert len(r.json()["content"]) == 100_000

    async def test_note_special_characters(self, test_client, api_key):
        """Notes with special characters, unicode, markdown."""
        special_titles = [
            "Note with 'quotes'",
            'Note with "double quotes"',
            "Note with <html> tags",
            "Note with émojis 🎓📚",
            "日本語のノート",
            "Note with\nnewlines\tin\tit",
            "SELECT * FROM notes; --",
        ]
        for title in special_titles:
            r = await test_client.post(
                "/api/v1/notes",
                json={"title": title, "content": f"Content: {title}"},
                headers=_h(api_key),
            )
            assert r.status_code in (200, 201), f"Failed with title: {title!r} - {r.text}"

    async def test_note_markdown_content(self, test_client, api_key):
        """Note with complex markdown content."""
        markdown = """# Heading 1
## Heading 2

- Bullet 1
- Bullet 2
  - Nested

```python
def hello():
    print("world")
```

| Col1 | Col2 |
|------|------|
| A    | B    |

> Blockquote

**bold** *italic* ~~strikethrough~~
"""
        r = await test_client.post(
            "/api/v1/notes",
            json={"title": "Markdown Note", "content": markdown},
            headers=_h(api_key),
        )
        assert r.status_code in (200, 201)

    async def test_note_rapid_update(self, test_client, api_key):
        """Update a note 30 times rapidly."""
        note = await _create_note(test_client, api_key, "Rapid Update")
        nid = note["id"]

        for i in range(30):
            r = await test_client.put(
                f"/api/v1/notes/{nid}",
                json={"content": f"Version {i}", "word_count": i * 10},
                headers=_h(api_key),
            )
            assert r.status_code == 200

        # Verify final state
        r = await test_client.get(f"/api/v1/notes/{nid}", headers=_h(api_key))
        assert r.status_code == 200
        assert r.json()["content"] == "Version 29"

    async def test_note_empty_title_rejected(self, test_client, api_key):
        """Note with empty title should be rejected."""
        r = await test_client.post(
            "/api/v1/notes",
            json={"title": "", "content": "stuff"},
            headers=_h(api_key),
        )
        assert r.status_code == 422

    async def test_note_linked_to_course(self, test_client, api_key):
        """Note linked to a course; verify enriched fields."""
        sem = await _create_semester(test_client, api_key)
        course = await _create_course(test_client, api_key, sem["id"], "NOTE01", "Note Course")
        note = await _create_note(test_client, api_key, "Linked Note", course_id=course["id"])

        r = await test_client.get(f"/api/v1/notes/{note['id']}", headers=_h(api_key))
        assert r.status_code == 200
        data = r.json()
        assert data["course_id"] == course["id"]


# ===========================================================================
# TAG STRESS TESTS
# ===========================================================================


class TestTagStress:
    """Stress tests for tags."""

    async def test_create_many_tags(self, test_client, api_key):
        """Create many tags."""
        for i in range(30):
            r = await test_client.post(
                "/api/v1/tags",
                json={"label": f"Tag-{i:03d}", "color": f"#{i * 8 % 256:02X}55AA"},
                headers=_h(api_key),
            )
            assert r.status_code in (200, 201), f"Failed tag {i}: {r.text}"

    async def test_duplicate_tag_label_rejected(self, test_client, api_key):
        """Duplicate tag labels should be rejected."""
        r1 = await test_client.post(
            "/api/v1/tags",
            json={"label": "UniqueLabel"},
            headers=_h(api_key),
        )
        assert r1.status_code in (200, 201)

        r2 = await test_client.post(
            "/api/v1/tags",
            json={"label": "UniqueLabel"},
            headers=_h(api_key),
        )
        assert r2.status_code in (400, 409, 422)


# ===========================================================================
# AUTH STRESS TESTS
# ===========================================================================


class TestAuthStress:
    """Stress tests for authentication."""

    async def test_missing_api_key(self, test_client):
        """All endpoints should reject requests without API key."""
        endpoints = [
            ("GET", "/api/v1/courses"),
            ("GET", "/api/v1/semesters"),
            ("GET", "/api/v1/academic-items"),
            ("GET", "/api/v1/notes"),
            ("GET", "/api/v1/tags"),
            ("POST", "/api/v1/courses"),
            ("POST", "/api/v1/semesters"),
        ]
        for method, url in endpoints:
            r = await test_client.request(method, url)
            assert r.status_code == 401, f"{method} {url} returned {r.status_code} without key"

    async def test_invalid_api_key(self, test_client):
        """Invalid API key should be rejected."""
        r = await test_client.get(
            "/api/v1/courses",
            headers={"X-API-Key": "wrong-key-totally-invalid"},
        )
        assert r.status_code == 401

    async def test_many_unauthorized_requests(self, test_client):
        """Repeated unauthorized requests should all return 401."""
        for _ in range(50):
            r = await test_client.get("/api/v1/courses")
            assert r.status_code == 401


# ===========================================================================
# MASS EDITOR STRESS TESTS
# ===========================================================================


class TestMassEditorStress:
    """Stress tests for bulk edit operations."""

    async def test_bulk_update_many_items(self, test_client, api_key):
        """Bulk update status on many items at once."""
        sem = await _create_semester(test_client, api_key)
        course = await _create_course(test_client, api_key, sem["id"], "BULK01", "Bulk Course")
        cid = course["id"]

        # Create 25 items
        item_ids = []
        for i in range(25):
            item = await _create_item(test_client, api_key, cid, name=f"Bulk {i}")
            item_ids.append(item["id"])

        # Bulk update status
        r = await test_client.post(
            "/api/v1/editor/academic-items",
            json={"item_ids": item_ids, "status": "InProgress"},
            headers=_h(api_key),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["updated_count"] == 25
        assert data["failed_count"] == 0

    async def test_bulk_update_with_invalid_ids(self, test_client, api_key):
        """Bulk update with mix of valid and invalid IDs."""
        sem = await _create_semester(test_client, api_key)
        course = await _create_course(test_client, api_key, sem["id"], "BULKINV", "Bulk Invalid")
        item = await _create_item(test_client, api_key, course["id"], name="Real Item")

        r = await test_client.post(
            "/api/v1/editor/academic-items",
            json={"item_ids": [item["id"], 99999, 99998], "status": "Graded"},
            headers=_h(api_key),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["updated_count"] >= 1
        assert data["failed_count"] == 2

    async def test_bulk_update_invalid_status(self, test_client, api_key):
        """Bulk update with invalid status should fail gracefully."""
        sem = await _create_semester(test_client, api_key)
        course = await _create_course(test_client, api_key, sem["id"], "BULKBAD", "Bulk Bad")
        item = await _create_item(test_client, api_key, course["id"], name="Status Item")

        r = await test_client.post(
            "/api/v1/editor/academic-items",
            json={"item_ids": [item["id"]], "status": "TotallyFakeStatus"},
            headers=_h(api_key),
        )
        assert r.status_code == 200
        data = r.json()
        assert data["updated_count"] == 0


# ===========================================================================
# CALENDAR STRESS TESTS
# ===========================================================================


class TestCalendarStress:
    """Stress tests for the calendar endpoint."""

    async def test_calendar_wide_date_range(self, test_client, api_key):
        """Calendar with a year-wide range."""
        r = await test_client.get(
            "/api/v1/calendar?start_date=2025-01-01&end_date=2025-12-31",
            headers=_h(api_key),
        )
        assert r.status_code == 200

    async def test_calendar_single_day(self, test_client, api_key):
        """Calendar for a single day."""
        r = await test_client.get(
            "/api/v1/calendar?start_date=2025-06-15&end_date=2025-06-15",
            headers=_h(api_key),
        )
        assert r.status_code == 200

    async def test_calendar_with_items(self, test_client, api_key):
        """Calendar shows items with due dates in range."""
        sem = await _create_semester(test_client, api_key)
        course = await _create_course(test_client, api_key, sem["id"], "CAL01", "Calendar Course")

        # Create items due on specific dates
        for day in range(1, 10):
            await _create_item(
                test_client, api_key, course["id"],
                name=f"Cal Item {day}",
                due_date=f"2025-10-{day:02d}T12:00:00",
            )

        r = await test_client.get(
            "/api/v1/calendar?start_date=2025-10-01&end_date=2025-10-31",
            headers=_h(api_key),
        )
        assert r.status_code == 200
        days = r.json()
        # Should have entries for days 1-9
        assert len(days) >= 9


# ===========================================================================
# HEALTH & SYSTEM STRESS TESTS
# ===========================================================================


class TestSystemStress:
    """Stress tests for system endpoints."""

    async def test_health_check_rapid(self, test_client, api_key):
        """Hit health check rapidly."""
        for _ in range(50):
            r = await test_client.get("/api/v1/health", headers=_h(api_key))
            assert r.status_code == 200

    async def test_system_status(self, test_client, api_key):
        """System status returns valid data."""
        r = await test_client.get("/api/v1/system/status", headers=_h(api_key))
        assert r.status_code == 200
        data = r.json()
        assert "version" in data


# ===========================================================================
# CONCURRENT-STYLE OPERATIONS
# ===========================================================================


class TestConcurrentOperations:
    """Simulate rapid sequential operations (async sessions don't support parallel writes)."""

    async def test_rapid_sequential_creates(self, test_client, api_key):
        """Create 20 resources in rapid sequence."""
        sem = await _create_semester(test_client, api_key)
        sid = sem["id"]

        for i in range(20):
            r = await test_client.post(
                "/api/v1/courses",
                json={"code": f"CON{i:03d}", "name": f"Concurrent {i}", "semester_id": sid},
                headers=_h(api_key),
            )
            assert r.status_code in (200, 201)

        # Verify all created
        r = await test_client.get(f"/api/v1/courses?semester_id={sid}", headers=_h(api_key))
        assert r.status_code == 200
        assert len(r.json()) == 20

    async def test_rapid_reads(self, test_client, api_key):
        """Many rapid read requests."""
        for _ in range(30):
            r = await test_client.get("/api/v1/courses", headers=_h(api_key))
            assert r.status_code == 200

    async def test_rapid_mixed_operations(self, test_client, api_key):
        """Rapid mix of reads and writes."""
        sem = await _create_semester(test_client, api_key)

        for i in range(30):
            if i % 3 == 0:
                r = await test_client.get("/api/v1/courses", headers=_h(api_key))
            elif i % 3 == 1:
                r = await test_client.post(
                    "/api/v1/courses",
                    json={"code": f"MIX{i:03d}", "name": f"Mixed {i}", "semester_id": sem["id"]},
                    headers=_h(api_key),
                )
            else:
                r = await test_client.get("/api/v1/notes", headers=_h(api_key))
            assert r.status_code in (200, 201), f"Op {i} got {r.status_code}: {r.text[:200]}"


# ===========================================================================
# EMPTY STATE & EDGE CASE TESTS
# ===========================================================================


class TestEmptyStateEdgeCases:
    """Test behavior when database is empty or inputs are edge cases."""

    async def test_list_empty_courses(self, test_client, api_key):
        """List courses when none exist."""
        r = await test_client.get("/api/v1/courses", headers=_h(api_key))
        assert r.status_code == 200
        assert r.json() == []

    async def test_list_empty_notes(self, test_client, api_key):
        """List notes when none exist."""
        r = await test_client.get("/api/v1/notes", headers=_h(api_key))
        assert r.status_code == 200
        data = r.json()
        # Notes endpoint may return paginated or raw list
        items = data["items"] if isinstance(data, dict) and "items" in data else data
        assert items == []

    async def test_list_empty_tags(self, test_client, api_key):
        """List tags when none exist."""
        r = await test_client.get("/api/v1/tags", headers=_h(api_key))
        assert r.status_code == 200
        assert r.json() == []

    async def test_empty_json_body(self, test_client, api_key):
        """POST with empty JSON body."""
        r = await test_client.post("/api/v1/courses", json={}, headers=_h(api_key))
        assert r.status_code == 422

    async def test_null_fields(self, test_client, api_key):
        """POST with explicit null values for optional fields."""
        sem = await _create_semester(test_client, api_key)
        r = await test_client.post(
            "/api/v1/courses",
            json={
                "code": "NULL01",
                "name": "Null Fields",
                "semester_id": sem["id"],
                "professor": None,
                "section": None,
                "credits": None,
                "color": None,
                "notes": None,
            },
            headers=_h(api_key),
        )
        assert r.status_code in (200, 201)

    async def test_extra_unknown_fields_ignored(self, test_client, api_key):
        """Extra unknown fields in request body should be ignored."""
        sem = await _create_semester(test_client, api_key)
        r = await test_client.post(
            "/api/v1/courses",
            json={
                "code": "EXTRA01",
                "name": "Extra Fields",
                "semester_id": sem["id"],
                "nonexistent_field": "should be ignored",
                "another_fake": 42,
            },
            headers=_h(api_key),
        )
        # Should succeed or fail validation — not crash
        assert r.status_code in (200, 201, 422)

    async def test_get_nonexistent_resources(self, test_client, api_key):
        """GET requests for non-existent IDs return 404."""
        endpoints = [
            "/api/v1/courses/99999",
            "/api/v1/academic-items/99999",
            "/api/v1/notes/99999",
            "/api/v1/semesters/99999",
            "/api/v1/tags/99999",
        ]
        for url in endpoints:
            r = await test_client.get(url, headers=_h(api_key))
            assert r.status_code == 404, f"{url} returned {r.status_code} instead of 404"

    async def test_very_large_id(self, test_client, api_key):
        """Very large ID should return 404, not crash."""
        r = await test_client.get("/api/v1/courses/2147483647", headers=_h(api_key))
        assert r.status_code in (404, 422)

    async def test_string_id_rejected(self, test_client, api_key):
        """String where int ID expected should be rejected."""
        r = await test_client.get("/api/v1/courses/abc", headers=_h(api_key))
        assert r.status_code == 422

    async def test_negative_id_rejected(self, test_client, api_key):
        """Negative ID should be rejected or return 404."""
        r = await test_client.get("/api/v1/courses/-1", headers=_h(api_key))
        assert r.status_code in (404, 422)
