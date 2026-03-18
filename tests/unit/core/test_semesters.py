"""Unit tests for semester management."""

from datetime import datetime

import pytest
import pytest_asyncio

from scholarr.db.models import Semester, TermEnum
from scholarr.schemas.semester import SemesterCreate, SemesterUpdate
from scholarr.services.semester_service import SemesterService


@pytest_asyncio.fixture
async def semester_service(async_session):
    """Create a SemesterService instance."""
    return SemesterService(async_session)


class TestCreateSemester:
    """Tests for semester creation."""

    async def test_create_semester(self, semester_service, sample_semester):
        """Test creating a new semester."""
        semester_data = SemesterCreate(
            name="Spring 2025",
            year=2025,
            term=TermEnum.SPRING,
            start_date=datetime(2025, 1, 15),
            end_date=datetime(2025, 5, 15),
        )

        semester = await semester_service.create_semester(semester_data)

        assert semester.name == "Spring 2025"
        assert semester.year == 2025
        assert semester.term == TermEnum.SPRING
        assert semester.active is False

    async def test_create_semester_with_active(self, semester_service):
        """Test creating an active semester."""
        semester_data = SemesterCreate(
            name="Summer 2025",
            year=2025,
            term=TermEnum.SUMMER,
            start_date=datetime(2025, 6, 1),
            end_date=datetime(2025, 8, 31),
            active=True,
        )

        semester = await semester_service.create_semester(semester_data)

        assert semester.active is True

    async def test_create_duplicate_semester(self, semester_service, sample_semester):
        """Test that duplicate year/term combinations are rejected."""
        semester_data = SemesterCreate(
            name="Different Name",
            year=sample_semester.year,
            term=sample_semester.term,
            start_date=datetime(2024, 9, 1),
            end_date=datetime(2024, 12, 31),
        )

        with pytest.raises(ValueError):
            await semester_service.create_semester(semester_data)


class TestGetSemester:
    """Tests for retrieving semesters."""

    async def test_get_semester(self, semester_service, sample_semester):
        """Test getting a semester by ID."""
        semester = await semester_service.get_semester(sample_semester.id)

        assert semester is not None
        assert semester.id == sample_semester.id
        assert semester.name == sample_semester.name

    async def test_get_nonexistent_semester(self, semester_service):
        """Test getting a non-existent semester."""
        semester = await semester_service.get_semester(9999)

        assert semester is None


class TestUpdateSemester:
    """Tests for updating semesters."""

    async def test_update_semester(self, semester_service, sample_semester):
        """Test updating a semester."""
        update_data = SemesterUpdate(
            name="Fall 2024 Updated",
            end_date=datetime(2024, 12, 20),
        )

        updated = await semester_service.update_semester(sample_semester.id, update_data)

        assert updated is not None
        assert updated.name == "Fall 2024 Updated"
        assert updated.end_date == datetime(2024, 12, 20)
        assert updated.year == sample_semester.year

    async def test_update_nonexistent_semester(self, semester_service):
        """Test updating a non-existent semester."""
        update_data = SemesterUpdate(name="Updated Name")

        updated = await semester_service.update_semester(9999, update_data)

        assert updated is None

    async def test_update_partial_semester(self, semester_service, sample_semester):
        """Test partial semester update."""
        original_year = sample_semester.year
        update_data = SemesterUpdate(name="Renamed Semester")

        updated = await semester_service.update_semester(sample_semester.id, update_data)

        assert updated is not None
        assert updated.name == "Renamed Semester"
        assert updated.year == original_year


class TestSetActiveSemester:
    """Tests for setting active semester."""

    async def test_set_active_semester(self, async_session, semester_service, sample_semester):
        """Test setting a semester as active."""
        # Create another semester
        other_semester = Semester(
            name="Winter 2025",
            year=2025,
            term=TermEnum.WINTER,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 4, 30),
            active=False,
        )
        async_session.add(other_semester)
        await async_session.commit()

        # Set other semester as active
        result = await semester_service.set_active_semester(other_semester.id)

        assert result is not None
        assert result.active is True

    async def test_set_active_deactivates_previous(self, async_session, semester_service, sample_semester):
        """Test that setting a semester active deactivates previous."""
        assert sample_semester.active is True

        other_semester = Semester(
            name="Winter 2025",
            year=2025,
            term=TermEnum.WINTER,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 4, 30),
            active=False,
        )
        async_session.add(other_semester)
        await async_session.commit()

        await semester_service.set_active_semester(other_semester.id)

        # Refresh to check
        refreshed = await semester_service.get_semester(sample_semester.id)
        assert refreshed.active is False


class TestDeleteSemester:
    """Tests for deleting semesters."""

    async def test_delete_semester(self, async_session, semester_service):
        """Test deleting a semester without courses."""
        semester = Semester(
            name="Test Delete",
            year=2025,
            term=TermEnum.SPRING,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 5, 31),
        )
        async_session.add(semester)
        await async_session.commit()

        success = await semester_service.delete_semester(semester.id)

        assert success is True
        deleted = await semester_service.get_semester(semester.id)
        assert deleted is None

    async def test_delete_nonexistent_semester(self, semester_service):
        """Test deleting a non-existent semester."""
        success = await semester_service.delete_semester(9999)

        assert success is False

    async def test_delete_semester_with_courses(
        self, async_session, semester_service, sample_semester, sample_course
    ):
        """Test deleting a semester with associated courses."""
        semester_id = sample_semester.id

        success = await semester_service.delete_semester(semester_id, cascade=True)

        assert success is True
        deleted = await semester_service.get_semester(semester_id)
        assert deleted is None


class TestListSemesters:
    """Tests for listing semesters."""

    async def test_list_semesters(self, async_session, semester_service, sample_semester):
        """Test listing all semesters."""
        # Add another semester
        semester2 = Semester(
            name="Winter 2025",
            year=2025,
            term=TermEnum.WINTER,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 4, 30),
        )
        async_session.add(semester2)
        await async_session.commit()

        semesters = await semester_service.list_semesters()

        assert len(semesters) >= 2

    async def test_list_semesters_by_year(self, async_session, semester_service, sample_semester):
        """Test listing semesters filtered by year."""
        # Add semester from different year
        semester2 = Semester(
            name="Fall 2025",
            year=2025,
            term=TermEnum.FALL,
            start_date=datetime(2025, 9, 1),
            end_date=datetime(2025, 12, 31),
        )
        async_session.add(semester2)
        await async_session.commit()

        semesters = await semester_service.list_semesters(year=sample_semester.year)

        assert all(s.year == sample_semester.year for s in semesters)

    async def test_get_active_semester(self, async_session, semester_service, sample_semester):
        """Test retrieving the active semester."""
        active = await semester_service.get_active_semester()

        assert active is not None
        assert active.active is True


class TestTermEnum:
    """Tests for term enumeration."""

    def test_term_enum_values(self):
        """Test that all term values are valid."""
        terms = [TermEnum.WINTER, TermEnum.SPRING, TermEnum.SUMMER, TermEnum.FALL]

        assert len(terms) == 4
        assert TermEnum.WINTER.value == "Winter"
        assert TermEnum.SPRING.value == "Spring"
        assert TermEnum.SUMMER.value == "Summer"
        assert TermEnum.FALL.value == "Fall"

    def test_term_enum_string_conversion(self):
        """Test string conversion of term enum."""
        term = TermEnum.FALL

        assert str(term) == "TermEnum.FALL"
        assert term.value == "Fall"
