"""Health check service for Scholarr."""

import os
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    source: str
    check_type: str
    message: str
    status: str  # "ok", "warning", "error"
    wiki_url: str | None = None


class HealthCheckService:
    """Service for performing health checks."""

    def __init__(self, session: AsyncSession):
        """Initialize health check service.

        Args:
            session: SQLAlchemy async session.
        """
        self.session = session

    async def check_database(self) -> HealthCheckResult:
        """Check database connectivity and health.

        Returns:
            HealthCheckResult: Health check result.
        """
        try:
            await self.session.execute(text("SELECT 1"))
            return HealthCheckResult(
                source="database",
                check_type="connectivity",
                message="Database connection successful",
                status="ok",
            )
        except Exception as e:
            return HealthCheckResult(
                source="database",
                check_type="connectivity",
                message=f"Database connection failed: {str(e)}",
                status="error",
                wiki_url="https://scholarr.docs/troubleshooting/database",
            )

    async def check_root_folders(self) -> list[HealthCheckResult]:
        """Check root folders existence and writability.

        Returns:
            list[HealthCheckResult]: List of health check results.
        """
        from sqlalchemy import select

        from scholarr.db.models import RootFolder

        result = await self.session.execute(select(RootFolder))
        folders = result.scalars().all()

        results = []

        for folder in folders:
            path = folder.path

            if not os.path.exists(path):
                results.append(
                    HealthCheckResult(
                        source=f"root_folder:{folder.id}",
                        check_type="existence",
                        message=f"Root folder does not exist: {path}",
                        status="error",
                        wiki_url="https://scholarr.docs/troubleshooting/folders",
                    )
                )
                continue

            if not os.access(path, os.W_OK):
                results.append(
                    HealthCheckResult(
                        source=f"root_folder:{folder.id}",
                        check_type="writability",
                        message=f"Root folder is not writable: {path}",
                        status="error",
                        wiki_url="https://scholarr.docs/troubleshooting/permissions",
                    )
                )
                continue

            results.append(
                HealthCheckResult(
                    source=f"root_folder:{folder.id}",
                    check_type="status",
                    message=f"Root folder healthy: {path}",
                    status="ok",
                )
            )

        return results

    async def check_courses(self) -> list[HealthCheckResult]:
        """Check courses configuration validity.

        Returns:
            list[HealthCheckResult]: List of health check results.
        """
        from sqlalchemy import select

        from scholarr.db.models import Course

        result = await self.session.execute(select(Course))
        courses = result.scalars().all()

        results = []

        for course in courses:
            if not course.code:
                results.append(
                    HealthCheckResult(
                        source=f"course:{course.id}",
                        check_type="configuration",
                        message=f"Course missing code: {course.name}",
                        status="warning",
                        wiki_url="https://scholarr.docs/troubleshooting/courses",
                    )
                )
            else:
                results.append(
                    HealthCheckResult(
                        source=f"course:{course.id}",
                        check_type="configuration",
                        message=f"Course configured correctly: {course.code}",
                        status="ok",
                    )
                )

        if not courses:
            results.append(
                HealthCheckResult(
                    source="courses",
                    check_type="configuration",
                    message="No courses configured",
                    status="warning",
                    wiki_url="https://scholarr.docs/quickstart",
                )
            )

        return results

    async def run_all(self) -> list[HealthCheckResult]:
        """Run all health checks.

        Returns:
            list[HealthCheckResult]: List of all health check results.
        """
        results = []
        results.append(await self.check_database())
        results.extend(await self.check_root_folders())
        results.extend(await self.check_courses())
        return results
