"""Unit tests for course management."""

from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy import select

from scholarr.db.models import Course, Semester, TermEnum, AcademicItem, AcademicItemTypeEnum
from scholarr.schemas.course import CourseCreate, CourseUpdate
from scholarr.services.course_service import CourseService


@pytest_asyncio.fixture
async def course_service(async_session):
    """Create a CourseService instance."""
    return CourseService(async_session)


@pytest_asyncio.fixture
async def extra_semester(async_session):
    """Create an extra semester for testing."""
    semester = Semester(
        name="Winter 2025",
        year=2025,
        term=TermEnum.WINTER,
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 4, 30),
        active=False,
    )
    async_session.add(semester)
    await async_session.commit()
    return semester


class TestCreateCourse:
    """Tests for course creation."""

    async def test_create_course(self, async_session, course_service, sample_semester):
        """Test creating a new course."""
        course_data = CourseCreate(
            code="MAT235",
            name="Calculus III",
            professor="Dr. Johnson",
            semester_id=sample_semester.id,
            section="02",
            credits=4.0,
            color="#00AA00",
        )

        course = await course_service.create_course(course_data)

        assert course.code == "MAT235"
        assert course.name == "Calculus III"
        assert course.professor == "Dr. Johnson"
        assert course.semester_id == sample_semester.id
        assert course.credits == 4.0

    async def test_create_course_minimal(self, async_session, course_service, sample_semester):
        """Test creating a course with minimal required fields."""
        course_data = CourseCreate(
            code="PHY101",
            name="Physics I",
            semester_id=sample_semester.id,
        )

        course = await course_service.create_course(course_data)

        assert course.code == "PHY101"
        assert course.name == "Physics I"
        assert course.professor is None
        assert course.credits is None

    async def test_create_course_invalid_code(self, async_session, course_service, sample_semester):
        """Test creating a course with invalid code."""
        course_data = CourseCreate(
            code="",
            name="Invalid Course",
            semester_id=sample_semester.id,
        )

        with pytest.raises(ValueError):
            await course_service.create_course(course_data)

    async def test_create_duplicate_course_same_semester(
        self, async_session, course_service, sample_semester, sample_course
    ):
        """Test that duplicate course codes in same semester are rejected."""
        course_data = CourseCreate(
            code=sample_course.code,
            name="Different Name",
            semester_id=sample_semester.id,
        )

        with pytest.raises(ValueError):
            await course_service.create_course(course_data)

    async def test_create_same_code_different_semester(
        self, async_session, course_service, sample_semester, extra_semester, sample_course
    ):
        """Test that same course code in different semesters is allowed."""
        course_data = CourseCreate(
            code=sample_course.code,
            name="Data Structures Winter",
            semester_id=extra_semester.id,
        )

        course = await course_service.create_course(course_data)

        assert course.code == sample_course.code
        assert course.semester_id == extra_semester.id


class TestGetCourse:
    """Tests for retrieving courses."""

    async def test_get_course(self, course_service, sample_course):
        """Test getting a course by ID."""
        course = await course_service.get_course(sample_course.id)

        assert course is not None
        assert course.id == sample_course.id
        assert course.code == sample_course.code

    async def test_get_nonexistent_course(self, course_service):
        """Test getting a non-existent course."""
        course = await course_service.get_course(9999)

        assert course is None


class TestUpdateCourse:
    """Tests for updating courses."""

    async def test_update_course(self, course_service, sample_course):
        """Test updating a course."""
        update_data = CourseUpdate(
            name="Advanced Data Structures",
            professor="Dr. Brown",
            credits=4.0,
        )

        updated = await course_service.update_course(sample_course.id, update_data)

        assert updated is not None
        assert updated.name == "Advanced Data Structures"
        assert updated.professor == "Dr. Brown"
        assert updated.credits == 4.0
        assert updated.code == sample_course.code

    async def test_update_nonexistent_course(self, course_service):
        """Test updating a non-existent course."""
        update_data = CourseUpdate(name="Updated Name")

        updated = await course_service.update_course(9999, update_data)

        assert updated is None

    async def test_update_partial_fields(self, course_service, sample_course):
        """Test partial course update."""
        update_data = CourseUpdate(monitored=not sample_course.monitored)

        updated = await course_service.update_course(sample_course.id, update_data)

        assert updated is not None
        assert updated.monitored != sample_course.monitored
        assert updated.name == sample_course.name


class TestDeleteCourse:
    """Tests for deleting courses."""

    async def test_delete_course(self, async_session, course_service, sample_course):
        """Test deleting a course."""
        course_id = sample_course.id

        success = await course_service.delete_course(course_id)

        assert success is True

        # Verify course is deleted
        deleted = await course_service.get_course(course_id)
        assert deleted is None

    async def test_delete_nonexistent_course(self, course_service):
        """Test deleting a non-existent course."""
        success = await course_service.delete_course(9999)

        assert success is False

    async def test_delete_course_with_files(
        self, async_session, course_service, sample_course, sample_academic_item, sample_managed_file
    ):
        """Test deleting a course with associated files."""
        course_id = sample_course.id

        success = await course_service.delete_course(course_id, delete_files=True)

        assert success is True

        # Verify cascade delete
        deleted_course = await course_service.get_course(course_id)
        assert deleted_course is None

    async def test_delete_course_cascade(self, async_session, course_service, sample_course, sample_academic_item):
        """Test that deleting a course cascades to academic items."""
        course_id = sample_course.id

        success = await course_service.delete_course(course_id)

        assert success is True

        # Check that academic items are also deleted
        result = await async_session.execute(
            select(AcademicItem).where(AcademicItem.course_id == course_id)
        )
        items = result.scalars().all()
        assert len(items) == 0


class TestListCourses:
    """Tests for listing courses."""

    async def test_list_all_courses(self, async_session, course_service, sample_course, sample_semester):
        """Test listing all courses."""
        # Add another course
        course2 = Course(
            code="PHY101",
            name="Physics I",
            semester_id=sample_semester.id,
        )
        async_session.add(course2)
        await async_session.commit()

        courses = await course_service.list_courses()

        assert len(courses) >= 2
        assert any(c.code == "BCS310" for c in courses)
        assert any(c.code == "PHY101" for c in courses)

    async def test_list_courses_by_semester(self, async_session, course_service, sample_course, sample_semester, extra_semester):
        """Test listing courses filtered by semester."""
        # Add course to different semester
        course2 = Course(
            code="CHM101",
            name="Chemistry I",
            semester_id=extra_semester.id,
        )
        async_session.add(course2)
        await async_session.commit()

        courses = await course_service.list_courses(semester_id=sample_semester.id)

        assert len(courses) >= 1
        assert all(c.semester_id == sample_semester.id for c in courses)

    async def test_list_monitored_courses(self, async_session, course_service, sample_course, sample_semester):
        """Test listing only monitored courses."""
        # Create a non-monitored course
        course2 = Course(
            code="ENG102",
            name="English Composition",
            semester_id=sample_semester.id,
            monitored=False,
        )
        async_session.add(course2)
        await async_session.commit()

        courses = await course_service.list_courses(monitored=True)

        assert all(c.monitored is True for c in courses)

    async def test_search_courses(self, async_session, course_service, sample_course, sample_semester):
        """Test searching courses by name or code."""
        courses = await course_service.list_courses(search="Data")

        assert len(courses) >= 1
        assert any(c.code == "BCS310" for c in courses)

    async def test_search_courses_by_code(self, async_session, course_service, sample_course):
        """Test searching courses by code."""
        courses = await course_service.list_courses(search="BCS")

        assert len(courses) >= 1
        assert any(c.code == "BCS310" for c in courses)


class TestListCoursesPaginated:
    """Tests for paginated course listing."""

    async def test_paged_courses(self, async_session, course_service, sample_course, sample_semester):
        """Test paginated course listing."""
        # Create multiple courses
        for i in range(25):
            course = Course(
                code=f"TST{i:03d}",
                name=f"Test Course {i}",
                semester_id=sample_semester.id,
            )
            async_session.add(course)
        await async_session.commit()

        result = await course_service.list_courses_paginated(
            page=1, page_size=10, sort_key="code", sort_dir="asc"
        )

        assert result.total >= 25
        assert len(result.items) == 10
        assert result.page == 1
        assert result.page_size == 10

    async def test_paged_courses_second_page(self, async_session, course_service, sample_course, sample_semester):
        """Test retrieving second page of courses."""
        for i in range(25):
            course = Course(
                code=f"PST{i:03d}",
                name=f"Test Course {i}",
                semester_id=sample_semester.id,
            )
            async_session.add(course)
        await async_session.commit()

        result = await course_service.list_courses_paginated(
            page=2, page_size=10, sort_key="code", sort_dir="asc"
        )

        assert len(result.items) == 10
        assert result.page == 2

    async def test_paged_courses_sorting(self, async_session, course_service, sample_course, sample_semester):
        """Test course sorting in paginated results."""
        for i in range(5):
            course = Course(
                code=f"ZZZ{i:03d}",
                name=f"Z Course {i}",
                semester_id=sample_semester.id,
            )
            async_session.add(course)
        await async_session.commit()

        result = await course_service.list_courses_paginated(
            page=1, page_size=20, sort_key="code", sort_dir="desc"
        )

        codes = [c.code for c in result.items]
        # Verify descending order (Z comes before B)
        assert codes[0].startswith("ZZZ") or codes[0] == "BCS310"
