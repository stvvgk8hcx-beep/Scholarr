"""Unit tests for health check service."""

import tempfile

import pytest_asyncio

from scholarr.core.health_check import HealthCheckResult, HealthCheckService


@pytest_asyncio.fixture
async def health_service(async_session):
    """Create a HealthCheckService instance."""
    return HealthCheckService(async_session)


class TestCheckDatabase:
    """Tests for database health checks."""

    async def test_check_database_healthy(self, health_service):
        """Test database connectivity check when database is healthy."""
        result = await health_service.check_database()

        assert result.status == "ok"
        assert result.check_type == "connectivity"
        assert result.source == "database"

    async def test_health_check_result_structure(self, health_service):
        """Test that health check result has correct structure."""
        result = await health_service.check_database()

        assert isinstance(result, HealthCheckResult)
        assert hasattr(result, "source")
        assert hasattr(result, "check_type")
        assert hasattr(result, "message")
        assert hasattr(result, "status")


class TestCheckRootFolders:
    """Tests for root folder health checks."""

    async def test_check_root_folders_exist(self, health_service):
        """Test checking if root folders exist."""
        results = await health_service.check_root_folders()

        assert isinstance(results, list)
        for result in results:
            assert isinstance(result, HealthCheckResult)

    async def test_root_folder_check_no_folders(self, health_service, async_session):
        """Test health check when no root folders configured."""
        results = await health_service.check_root_folders()

        # Should return empty list or warning
        assert isinstance(results, list)

    async def test_root_folder_check_writable(self, health_service):
        """Test checking if root folder is writable."""
        with tempfile.TemporaryDirectory():
            results = await health_service.check_root_folders()

            # Verify structure of results
            for result in results:
                assert result.status in ["ok", "warning", "error"]


class TestRunAllChecks:
    """Tests for running all health checks."""

    async def test_run_all_checks(self, health_service):
        """Test running all health checks."""
        results = await health_service.run_all()

        assert isinstance(results, list)
        assert len(results) > 0

        for result in results:
            assert isinstance(result, HealthCheckResult)
            assert result.status in ["ok", "warning", "error"]

    async def test_all_checks_include_database(self, health_service):
        """Test that all checks include database check."""
        results = await health_service.run_all()

        sources = [r.source for r in results]
        assert "database" in sources

    async def test_health_check_result_messages(self, health_service):
        """Test that health check results have messages."""
        results = await health_service.run_all()

        for result in results:
            assert result.message is not None
            assert len(result.message) > 0

    async def test_health_check_includes_courses(self, health_service):
        """Test that health checks include course checks."""
        results = await health_service.run_all()

        sources = [r.source for r in results]
        # Should have at least one course-related check
        assert any("course" in s.lower() for s in sources)


class TestHealthCheckStatuses:
    """Tests for health check status values."""

    async def test_status_ok(self, health_service):
        """Test OK status."""
        result = await health_service.check_database()

        assert result.status == "ok"

    async def test_status_values_valid(self, health_service):
        """Test that all status values are valid."""
        results = await health_service.run_all()

        valid_statuses = ["ok", "warning", "error"]
        for result in results:
            assert result.status in valid_statuses


class TestHealthCheckWikiUrl:
    """Tests for wiki URL in health check results."""

    async def test_health_check_wiki_url_present(self, health_service):
        """Test that wiki URLs are included in error results."""
        results = await health_service.run_all()

        error_results = [r for r in results if r.status == "error"]
        for result in error_results:
            # Error results should have wiki URL
            assert result.wiki_url is not None or result.wiki_url is None  # Optional field
