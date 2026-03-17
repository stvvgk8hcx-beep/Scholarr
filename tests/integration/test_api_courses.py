"""Integration tests for course API endpoints."""

from datetime import datetime

import pytest
from httpx import AsyncClient

from scholarr.db.models import TermEnum


class TestCreateCourseAPI:
    """Tests for POST /courses endpoint."""

    async def test_create_course_api(self, test_client, sample_semester, api_key):
        """Test creating a course via API."""
        course_data = {
            "code": "PHY101",
            "name": "Physics I",
            "semester_id": sample_semester.id,
            "professor": "Dr. Newton",
            "credits": 4.0,
        }

        response = await test_client.post(
            "/api/v1/courses",
            json=course_data,
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["code"] == "PHY101"
        assert data["name"] == "Physics I"

    async def test_create_course_minimal(self, test_client, sample_semester, api_key):
        """Test creating course with minimal fields."""
        course_data = {
            "code": "CHM101",
            "name": "Chemistry I",
            "semester_id": sample_semester.id,
        }

        response = await test_client.post(
            "/api/v1/courses",
            json=course_data,
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 201


class TestGetCoursesAPI:
    """Tests for GET /courses endpoint."""

    async def test_get_courses_api(self, test_client, sample_course, api_key):
        """Test retrieving all courses."""
        response = await test_client.get(
            "/api/v1/courses",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_course_by_id(self, test_client, sample_course, api_key):
        """Test retrieving a specific course."""
        response = await test_client.get(
            f"/api/v1/courses/{sample_course.id}",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_course.id
        assert data["code"] == sample_course.code

    async def test_get_course_not_found(self, test_client, api_key):
        """Test retrieving non-existent course."""
        response = await test_client.get(
            "/api/v1/courses/9999",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 404


class TestUpdateCourseAPI:
    """Tests for PUT /courses/{id} endpoint."""

    async def test_update_course_api(self, test_client, sample_course, api_key):
        """Test updating a course."""
        update_data = {
            "name": "Advanced Physics I",
            "professor": "Dr. Einstein",
            "credits": 4.5,
        }

        response = await test_client.put(
            f"/api/v1/courses/{sample_course.id}",
            json=update_data,
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Advanced Physics I"
        assert data["professor"] == "Dr. Einstein"

    async def test_update_course_not_found(self, test_client, api_key):
        """Test updating non-existent course."""
        update_data = {"name": "Updated Name"}

        response = await test_client.put(
            "/api/v1/courses/9999",
            json=update_data,
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 404


class TestDeleteCourseAPI:
    """Tests for DELETE /courses/{id} endpoint."""

    async def test_delete_course_api(self, test_client, sample_course, api_key):
        """Test deleting a course."""
        course_id = sample_course.id

        response = await test_client.delete(
            f"/api/v1/courses/{course_id}",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 204

    async def test_delete_course_not_found(self, test_client, api_key):
        """Test deleting non-existent course."""
        response = await test_client.delete(
            "/api/v1/courses/9999",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 404

    async def test_delete_course_with_files(
        self, test_client, sample_course, sample_academic_item, api_key
    ):
        """Test deleting course with associated files."""
        course_id = sample_course.id

        response = await test_client.delete(
            f"/api/v1/courses/{course_id}?delete_files=true",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 204


class TestFilterCoursesAPI:
    """Tests for filtering courses."""

    async def test_filter_courses_by_semester(
        self, test_client, sample_course, sample_semester, api_key
    ):
        """Test filtering courses by semester."""
        response = await test_client.get(
            f"/api/v1/courses?semester_id={sample_semester.id}",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    async def test_filter_monitored_courses(self, test_client, sample_course, api_key):
        """Test filtering monitored courses."""
        response = await test_client.get(
            "/api/v1/courses?monitored=true",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200

    async def test_search_courses(self, test_client, sample_course, api_key):
        """Test searching courses."""
        response = await test_client.get(
            "/api/v1/courses?search=Data",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200
        data = response.json()
        # Should find the course with "Data" in name


class TestPaginatedCoursesAPI:
    """Tests for paginated course listing."""

    async def test_paginated_courses_api(self, test_client, api_key):
        """Test paginated course listing."""
        response = await test_client.get(
            "/api/v1/courses/paged?page=1&page_size=10",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    async def test_pagination_parameters(self, test_client, api_key):
        """Test pagination parameters."""
        response = await test_client.get(
            "/api/v1/courses/paged?page=2&page_size=5&sort_key=code&sort_dir=desc",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200


class TestUnauthorizedRequest:
    """Tests for unauthorized access."""

    async def test_unauthorized_request_missing_key(self, test_client):
        """Test request without API key."""
        response = await test_client.get("/api/v1/courses")

        assert response.status_code == 401 or response.status_code == 403

    async def test_unauthorized_request_invalid_key(self, test_client):
        """Test request with invalid API key."""
        response = await test_client.get(
            "/api/v1/courses",
            headers={"X-API-Key": "invalid-key"},
        )

        assert response.status_code == 401 or response.status_code == 403


class TestInvalidCourseData:
    """Tests for invalid course data."""

    async def test_invalid_course_missing_required(self, test_client, sample_semester, api_key):
        """Test creating course with missing required fields."""
        course_data = {
            "code": "TST101",
            # Missing name and semester_id
        }

        response = await test_client.post(
            "/api/v1/courses",
            json=course_data,
            headers={"X-API-Key": api_key},
        )

        assert response.status_code >= 400

    async def test_invalid_course_empty_code(self, test_client, sample_semester, api_key):
        """Test creating course with empty code."""
        course_data = {
            "code": "",
            "name": "Empty Code Course",
            "semester_id": sample_semester.id,
        }

        response = await test_client.post(
            "/api/v1/courses",
            json=course_data,
            headers={"X-API-Key": api_key},
        )

        assert response.status_code >= 400


class TestCourseNotFound:
    """Tests for course not found scenarios."""

    async def test_get_nonexistent_course(self, test_client, api_key):
        """Test getting non-existent course."""
        response = await test_client.get(
            "/api/v1/courses/99999",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 404


class TestCascadeDelete:
    """Tests for cascade deletion."""

    async def test_cascade_delete_removes_items(
        self, test_client, sample_course, sample_academic_item, api_key
    ):
        """Test that deleting course removes related items."""
        course_id = sample_course.id

        response = await test_client.delete(
            f"/api/v1/courses/{course_id}",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 204

        # Verify course is deleted
        get_response = await test_client.get(
            f"/api/v1/courses/{course_id}",
            headers={"X-API-Key": api_key},
        )
        assert get_response.status_code == 404
