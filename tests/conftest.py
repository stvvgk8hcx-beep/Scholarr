"""Shared test fixtures and configuration."""

import tempfile
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from fastapi import Header, HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from scholarr.app import create_app
from scholarr.core.security import verify_api_key
from scholarr.db.base import Base
from scholarr.db.models import (
    AcademicItem,
    AcademicItemStatusEnum,
    AcademicItemTypeEnum,
    Course,
    ManagedFile,
    Semester,
    Tag,
    TermEnum,
)
from scholarr.db.session import get_db_session


@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory SQLite test database session."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session_local = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session_local() as session:
        yield session

    await engine.dispose()


_TEST_API_KEY = "test-api-key-12345"


@pytest_asyncio.fixture
async def test_client(async_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create an AsyncClient wired to the FastAPI app."""
    app = create_app()

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield async_session

    async def override_verify_api_key(x_api_key: str | None = Header(None)) -> str:
        if not x_api_key:
            raise HTTPException(status_code=401, detail="API key missing")
        if x_api_key != _TEST_API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return x_api_key

    app.dependency_overrides[get_db_session] = override_get_db
    app.dependency_overrides[verify_api_key] = override_verify_api_key

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def api_key() -> str:
    """Test API key."""
    return _TEST_API_KEY


@pytest.fixture
def temp_directory() -> AsyncGenerator[str, None]:
    """Create a temporary directory for file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest_asyncio.fixture
async def sample_semester(async_session: AsyncSession) -> Semester:
    """Create a sample semester for testing."""
    semester = Semester(
        name="Fall 2024",
        year=2024,
        term=TermEnum.FALL,
        start_date=datetime(2024, 9, 1),
        end_date=datetime(2024, 12, 15),
        active=True,
    )
    async_session.add(semester)
    await async_session.commit()
    return semester


@pytest_asyncio.fixture
async def sample_tag(async_session: AsyncSession) -> Tag:
    """Create a sample tag for testing."""
    tag = Tag(label="Core Course", color="#FF5733")
    async_session.add(tag)
    await async_session.commit()
    return tag


@pytest_asyncio.fixture
async def sample_course(
    async_session: AsyncSession, sample_semester: Semester
) -> Course:
    """Create a sample course for testing."""
    course = Course(
        code="BCS310",
        name="Data Structures",
        professor="Dr. Smith",
        semester_id=sample_semester.id,
        section="01",
        credits=3.0,
        color="#0066CC",
        monitored=True,
    )
    async_session.add(course)
    await async_session.commit()
    return course


@pytest_asyncio.fixture
async def sample_academic_item(
    async_session: AsyncSession, sample_course: Course
) -> AcademicItem:
    """Create a sample academic item for testing."""
    item = AcademicItem(
        course_id=sample_course.id,
        type=AcademicItemTypeEnum.ASSIGNMENT,
        name="Assignment 3",
        number="3",
        topic="Binary Search Trees",
        due_date=datetime.now(UTC) + timedelta(days=7),
        status=AcademicItemStatusEnum.IN_PROGRESS,
        grade=None,
        weight=10.0,
    )
    async_session.add(item)
    await async_session.commit()
    return item


@pytest_asyncio.fixture
async def sample_managed_file(
    async_session: AsyncSession, sample_academic_item: AcademicItem
) -> ManagedFile:
    """Create a sample managed file for testing."""
    managed_file = ManagedFile(
        academic_item_id=sample_academic_item.id,
        path="/library/BCS310/Assignment/Assignment_3.pdf",
        original_path="/inbox/BCS310_Assignment3.pdf",
        size=1024000,
        format="pdf",
        quality="highest",
        version=1,
        hash="abc123def456",
        original_filename="BCS310_Assignment3.pdf",
    )
    async_session.add(managed_file)
    await async_session.commit()
    return managed_file


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
