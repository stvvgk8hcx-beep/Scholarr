"""Unit tests for academic items."""

from datetime import datetime, timedelta

import pytest_asyncio

from scholarr.db.models import AcademicItem, AcademicItemStatusEnum, AcademicItemTypeEnum
from scholarr.schemas.academic_item import AcademicItemCreate, AcademicItemUpdate
from scholarr.services.academic_item_service import AcademicItemService


@pytest_asyncio.fixture
async def academic_item_service(async_session):
    """Create an AcademicItemService instance."""
    return AcademicItemService(async_session)


class TestCreateAcademicItem:
    """Tests for academic item creation."""

    async def test_create_item(self, academic_item_service, sample_course):
        """Test creating a new academic item."""
        item_data = AcademicItemCreate(
            course_id=sample_course.id,
            type=AcademicItemTypeEnum.LAB,
            name="Lab 4",
            number="4",
            topic="Recursion",
            due_date=datetime.now() + timedelta(days=7),
            status=AcademicItemStatusEnum.IN_PROGRESS,
        )

        item = await academic_item_service.create_item(item_data)

        assert item.type == AcademicItemTypeEnum.LAB
        assert item.name == "Lab 4"
        assert item.number == "4"
        assert item.course_id == sample_course.id

    async def test_create_item_minimal(self, academic_item_service, sample_course):
        """Test creating an item with minimal fields."""
        item_data = AcademicItemCreate(
            course_id=sample_course.id,
            type=AcademicItemTypeEnum.EXAM,
            name="Midterm Exam",
        )

        item = await academic_item_service.create_item(item_data)

        assert item.type == AcademicItemTypeEnum.EXAM
        assert item.due_date is None
        assert item.grade is None

    async def test_create_item_with_grade(self, academic_item_service, sample_course):
        """Test creating an item with grade."""
        item_data = AcademicItemCreate(
            course_id=sample_course.id,
            type=AcademicItemTypeEnum.ASSIGNMENT,
            name="Assignment 1",
            grade=95.5,
            status=AcademicItemStatusEnum.GRADED,
        )

        item = await academic_item_service.create_item(item_data)

        assert item.grade == 95.5
        assert item.status == AcademicItemStatusEnum.GRADED


class TestGetAcademicItem:
    """Tests for retrieving academic items."""

    async def test_get_item(self, academic_item_service, sample_academic_item):
        """Test getting an academic item by ID."""
        item = await academic_item_service.get_item(sample_academic_item.id)

        assert item is not None
        assert item.id == sample_academic_item.id
        assert item.name == sample_academic_item.name

    async def test_get_nonexistent_item(self, academic_item_service):
        """Test getting a non-existent item."""
        item = await academic_item_service.get_item(9999)

        assert item is None


class TestUpdateAcademicItem:
    """Tests for updating academic items."""

    async def test_update_item(self, academic_item_service, sample_academic_item):
        """Test updating an academic item."""
        update_data = AcademicItemUpdate(
            name="Assignment 3 Revised",
            status=AcademicItemStatusEnum.SUBMITTED,
            grade=92.0,
        )

        updated = await academic_item_service.update_item(sample_academic_item.id, update_data)

        assert updated is not None
        assert updated.name == "Assignment 3 Revised"
        assert updated.status == AcademicItemStatusEnum.SUBMITTED
        assert updated.grade == 92.0

    async def test_update_nonexistent_item(self, academic_item_service):
        """Test updating a non-existent item."""
        update_data = AcademicItemUpdate(name="Updated")

        updated = await academic_item_service.update_item(9999, update_data)

        assert updated is None

    async def test_update_partial_item(self, academic_item_service, sample_academic_item):
        """Test partial item update."""
        update_data = AcademicItemUpdate(status=AcademicItemStatusEnum.COMPLETE)

        updated = await academic_item_service.update_item(sample_academic_item.id, update_data)

        assert updated is not None
        assert updated.status == AcademicItemStatusEnum.COMPLETE
        assert updated.name == sample_academic_item.name


class TestDeleteAcademicItem:
    """Tests for deleting academic items."""

    async def test_delete_item(self, academic_item_service, sample_academic_item):
        """Test deleting an academic item."""
        item_id = sample_academic_item.id

        success = await academic_item_service.delete_item(item_id)

        assert success is True

        deleted = await academic_item_service.get_item(item_id)
        assert deleted is None

    async def test_delete_nonexistent_item(self, academic_item_service):
        """Test deleting a non-existent item."""
        success = await academic_item_service.delete_item(9999)

        assert success is False

    async def test_delete_item_with_files(
        self, academic_item_service, sample_academic_item, sample_managed_file
    ):
        """Test deleting an item with associated files."""
        item_id = sample_academic_item.id

        success = await academic_item_service.delete_item(item_id, delete_files=True)

        assert success is True


class TestFilterAcademicItems:
    """Tests for filtering academic items."""

    async def test_filter_by_status(self, async_session, academic_item_service, sample_course):
        """Test filtering items by status."""
        # Create multiple items with different statuses
        for status in [AcademicItemStatusEnum.NOT_STARTED, AcademicItemStatusEnum.IN_PROGRESS]:
            item = AcademicItem(
                course_id=sample_course.id,
                type=AcademicItemTypeEnum.ASSIGNMENT,
                name=f"Assignment {status.value}",
                status=status,
            )
            async_session.add(item)
        await async_session.commit()

        items = await academic_item_service.list_items(
            course_id=sample_course.id, status=AcademicItemStatusEnum.IN_PROGRESS
        )

        assert all(item.status == AcademicItemStatusEnum.IN_PROGRESS for item in items)

    async def test_filter_by_type(self, async_session, academic_item_service, sample_course):
        """Test filtering items by type."""
        # Create items of different types
        for item_type in [AcademicItemTypeEnum.LAB, AcademicItemTypeEnum.EXAM]:
            item = AcademicItem(
                course_id=sample_course.id,
                type=item_type,
                name=f"Item {item_type.value}",
            )
            async_session.add(item)
        await async_session.commit()

        items = await academic_item_service.list_items(
            course_id=sample_course.id, item_type=AcademicItemTypeEnum.LAB
        )

        assert all(item.type == AcademicItemTypeEnum.LAB for item in items)

    async def test_filter_overdue(self, async_session, academic_item_service, sample_course):
        """Test filtering overdue items."""
        # Create an overdue item
        overdue_item = AcademicItem(
            course_id=sample_course.id,
            type=AcademicItemTypeEnum.ASSIGNMENT,
            name="Overdue Assignment",
            due_date=datetime.now() - timedelta(days=5),
            status=AcademicItemStatusEnum.NOT_STARTED,
        )
        async_session.add(overdue_item)
        await async_session.commit()

        overdue_items = await academic_item_service.list_overdue_items(sample_course.id)

        assert len(overdue_items) > 0
        assert any(item.id == overdue_item.id for item in overdue_items)


class TestUpcomingDeadlines:
    """Tests for upcoming deadlines."""

    async def test_upcoming_deadlines(self, async_session, academic_item_service, sample_course):
        """Test retrieving upcoming deadlines."""
        # Create items with future due dates
        for i in range(3):
            item = AcademicItem(
                course_id=sample_course.id,
                type=AcademicItemTypeEnum.ASSIGNMENT,
                name=f"Future Assignment {i}",
                due_date=datetime.now() + timedelta(days=i + 1),
            )
            async_session.add(item)
        await async_session.commit()

        upcoming = await academic_item_service.list_upcoming_deadlines(
            course_id=sample_course.id, days=7
        )

        assert len(upcoming) >= 3

    async def test_upcoming_deadlines_filter_period(self, async_session, academic_item_service, sample_course):
        """Test upcoming deadlines within specific period."""
        # Create items at various distances
        near_item = AcademicItem(
            course_id=sample_course.id,
            type=AcademicItemTypeEnum.ASSIGNMENT,
            name="Due Soon",
            due_date=datetime.now() + timedelta(days=2),
        )
        far_item = AcademicItem(
            course_id=sample_course.id,
            type=AcademicItemTypeEnum.ASSIGNMENT,
            name="Due Later",
            due_date=datetime.now() + timedelta(days=30),
        )
        async_session.add(near_item)
        async_session.add(far_item)
        await async_session.commit()

        upcoming = await academic_item_service.list_upcoming_deadlines(
            course_id=sample_course.id, days=7
        )

        assert any(item.name == "Due Soon" for item in upcoming)
        assert not any(item.name == "Due Later" for item in upcoming)


class TestPaginatedItems:
    """Tests for paginated item listing."""

    async def test_paged_items(self, async_session, academic_item_service, sample_course):
        """Test paginated item listing."""
        # Create multiple items
        for i in range(25):
            item = AcademicItem(
                course_id=sample_course.id,
                type=AcademicItemTypeEnum.ASSIGNMENT,
                name=f"Assignment {i}",
            )
            async_session.add(item)
        await async_session.commit()

        result = await academic_item_service.list_items_paginated(
            page=1, page_size=10, course_id=sample_course.id
        )

        assert result.total >= 25
        assert len(result.items) == 10


class TestAllItemTypes:
    """Tests for all academic item types."""

    async def test_all_13_types(self, async_session, academic_item_service, sample_course):
        """Test that all 13 item types can be created."""
        types = [
            AcademicItemTypeEnum.ASSIGNMENT,
            AcademicItemTypeEnum.LAB,
            AcademicItemTypeEnum.LECTURE,
            AcademicItemTypeEnum.EXAM,
            AcademicItemTypeEnum.PAPER,
            AcademicItemTypeEnum.PROJECT,
            AcademicItemTypeEnum.NOTES,
            AcademicItemTypeEnum.SYLLABUS,
            AcademicItemTypeEnum.TEXTBOOK,
            AcademicItemTypeEnum.SLIDES,
            AcademicItemTypeEnum.TUTORIAL,
            AcademicItemTypeEnum.QUIZ,
            AcademicItemTypeEnum.OTHER,
        ]

        for item_type in types:
            item = AcademicItem(
                course_id=sample_course.id,
                type=item_type,
                name=f"Test {item_type.value}",
            )
            async_session.add(item)
        await async_session.commit()

        items = await academic_item_service.list_items(course_id=sample_course.id)

        assert len(items) >= 13


class TestAllItemStatuses:
    """Tests for all academic item statuses."""

    async def test_all_7_statuses(self, async_session, academic_item_service, sample_course):
        """Test that all 7 statuses are valid."""
        statuses = [
            AcademicItemStatusEnum.NOT_STARTED,
            AcademicItemStatusEnum.IN_PROGRESS,
            AcademicItemStatusEnum.SUBMITTED,
            AcademicItemStatusEnum.GRADED,
            AcademicItemStatusEnum.LATE,
            AcademicItemStatusEnum.INCOMPLETE,
            AcademicItemStatusEnum.COMPLETE,
        ]

        for status in statuses:
            item = AcademicItem(
                course_id=sample_course.id,
                type=AcademicItemTypeEnum.ASSIGNMENT,
                name=f"Item {status.value}",
                status=status,
            )
            async_session.add(item)
        await async_session.commit()

        items = await academic_item_service.list_items(course_id=sample_course.id)

        assert len(items) >= 7


class TestGradeValidation:
    """Tests for grade validation."""

    async def test_grade_validation_numeric(self, academic_item_service, sample_course):
        """Test numeric grade validation."""
        item_data = AcademicItemCreate(
            course_id=sample_course.id,
            type=AcademicItemTypeEnum.EXAM,
            name="Exam 1",
            grade=87.5,
        )

        item = await academic_item_service.create_item(item_data)

        assert item.grade == 87.5

    async def test_grade_validation_percentage(self, academic_item_service, sample_course):
        """Test percentage grade validation."""
        item_data = AcademicItemCreate(
            course_id=sample_course.id,
            type=AcademicItemTypeEnum.EXAM,
            name="Exam 2",
            grade=100.0,
        )

        item = await academic_item_service.create_item(item_data)

        assert item.grade == 100.0

    async def test_weight_field(self, academic_item_service, sample_course):
        """Test item weight field."""
        item_data = AcademicItemCreate(
            course_id=sample_course.id,
            type=AcademicItemTypeEnum.EXAM,
            name="Final Exam",
            weight=40.0,
        )

        item = await academic_item_service.create_item(item_data)

        assert item.weight == 40.0
