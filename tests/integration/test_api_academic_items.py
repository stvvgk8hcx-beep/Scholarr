"""Integration tests for academic items API endpoints."""

from datetime import datetime, timedelta

import pytest


class TestCreateItemAPI:
    """Tests for creating academic items via API."""

    async def test_create_item_api(self, test_client, sample_course, api_key):
        """Test creating an academic item."""
        item_data = {
            "course_id": sample_course.id,
            "type": "Lab",
            "name": "Lab 5",
            "number": "5",
            "topic": "Sorting Algorithms",
            "due_date": (datetime.now() + timedelta(days=7)).isoformat(),
        }

        response = await test_client.post(
            "/api/v1/academic-items",
            json=item_data,
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Lab 5"
        assert data["type"] == "Lab"

    async def test_create_item_minimal(self, test_client, sample_course, api_key):
        """Test creating item with minimal fields."""
        item_data = {
            "course_id": sample_course.id,
            "type": "Exam",
            "name": "Midterm Exam",
        }

        response = await test_client.post(
            "/api/v1/academic-items",
            json=item_data,
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 201


class TestGetItemsAPI:
    """Tests for retrieving academic items."""

    async def test_get_items_api(self, test_client, sample_academic_item, api_key):
        """Test retrieving all items."""
        response = await test_client.get(
            f"/api/v1/academic-items?course_id={sample_academic_item.course_id}",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_get_item_by_id(self, test_client, sample_academic_item, api_key):
        """Test retrieving specific item."""
        response = await test_client.get(
            f"/api/v1/academic-items/{sample_academic_item.id}",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_academic_item.id


class TestUpcomingItemsAPI:
    """Tests for upcoming deadlines."""

    async def test_upcoming_items_api(self, test_client, sample_course, api_key):
        """Test getting upcoming items."""
        response = await test_client.get(
            f"/api/v1/academic-items/upcoming?course_id={sample_course.id}",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200


class TestFilterByStatusAPI:
    """Tests for filtering by status."""

    async def test_filter_by_status_api(self, test_client, sample_course, api_key):
        """Test filtering items by status."""
        response = await test_client.get(
            f"/api/v1/academic-items?course_id={sample_course.id}&status=InProgress",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200


class TestPaginationAPI:
    """Tests for paginated item listing."""

    async def test_pagination_api(self, test_client, sample_course, api_key):
        """Test paginated item listing."""
        response = await test_client.get(
            f"/api/v1/academic-items/paged?course_id={sample_course.id}&page=1&page_size=10",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 200


class TestDeleteWithFilesAPI:
    """Tests for deleting items with files."""

    async def test_delete_with_files_api(self, test_client, sample_academic_item, api_key):
        """Test deleting item with associated files."""
        item_id = sample_academic_item.id

        response = await test_client.delete(
            f"/api/v1/academic-items/{item_id}?delete_files=true",
            headers={"X-API-Key": api_key},
        )

        assert response.status_code == 204 or response.status_code == 200
