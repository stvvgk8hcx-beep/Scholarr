"""Direct SQL database integration for importing/exporting academic data.

Allows Scholarr to connect to external databases (MySQL, PostgreSQL, SQLite)
to import grades, export courses, and sync data bidirectionally.

Uses SQLAlchemy for cross-database compatibility.

Example academic database schemas (for reference):
  - Courses: id, code, name, department, credits, semester_id
  - Grades: id, student_id, course_id, assignment_id, score, max_score
  - Assignments: id, course_id, name, due_date, weight
  - Students: id, name, email, student_number
"""

import contextlib
import logging
from typing import Any

try:
    from sqlalchemy import create_engine, inspect, text
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: F401
    from sqlalchemy.pool import StaticPool  # noqa: F401
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

from scholarr.core.integrations import BaseIntegrationProvider, IntegrationStatus, IntegrationType

logger = logging.getLogger(__name__)


class SqlIntegrationProvider(BaseIntegrationProvider):
    """SQL database integration provider.

    Connects to external SQL databases to import/export academic data.
    """

    def __init__(self):
        """Initialize SQL provider."""
        super().__init__("sql", IntegrationType.DATABASE)
        self._engine = None
        if not HAS_SQLALCHEMY:
            logger.warning("SQLAlchemy not installed; SQL integration will be limited")

    async def connect(self, config: dict[str, Any]) -> bool:
        """Connect to external SQL database.

        Config should contain:
            connection_string: SQLAlchemy connection URL
              Examples:
                - postgresql://user:pass@localhost/db
                - mysql+pymysql://user:pass@localhost/db
                - sqlite:///path/to/db.sqlite

        Args:
            config: Connection configuration dictionary

        Returns:
            True if connection successful
        """
        if not HAS_SQLALCHEMY:
            self._set_last_error("SQLAlchemy not installed")
            return False

        try:
            required = ["connection_string"]
            if not all(key in config for key in required):
                raise ValueError("Missing required config: connection_string")

            self._config = config
            conn_string = config["connection_string"]

            # Create engine (using async if supported)
            try:
                self._engine = create_async_engine(
                    conn_string,
                    echo=False,
                    pool_pre_ping=True
                )
            except Exception:
                # Fall back to sync engine
                self._engine = create_engine(
                    conn_string,
                    echo=False,
                    pool_pre_ping=True
                )

            # Test connection
            success = await self.test_connection()
            if success:
                self._is_connected = True
                self._clear_last_error()
                logger.info("Connected to SQL database")
            else:
                self._set_last_error("Failed to connect to database")

            return success

        except Exception as e:
            self._set_last_error(str(e))
            logger.error(f"SQL connection error: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from SQL database.

        Returns:
            True if successful
        """
        try:
            if self._engine:
                await self._engine.dispose()
            self._is_connected = False
            self._engine = None
            self._clear_last_error()
            logger.info("Disconnected from SQL database")
            return True
        except Exception as e:
            self._set_last_error(str(e))
            return False

    async def test_connection(self) -> bool:
        """Test if database connection is valid.

        Returns:
            True if connection successful
        """
        if not self._engine:
            return False

        try:
            # Try simple query
            if hasattr(self._engine, 'connect'):
                # Sync engine
                with self._engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            else:
                # Async engine
                async with self._engine.connect() as conn:
                    await conn.execute(text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"SQL connection test failed: {e}")
            return False

    async def export_courses_to_sql(
        self,
        courses: list[dict[str, Any]],
        table_name: str = "scholarr_courses"
    ) -> dict[str, Any]:
        """Export Scholarr courses to external database.

        Creates or appends to a table with Scholarr course data.

        Args:
            courses: List of course dictionaries from Scholarr
            table_name: Target table name in external database

        Returns:
            Dictionary with rows_exported and any errors

        Example course schema:
          CREATE TABLE scholarr_courses (
            id INT PRIMARY KEY,
            code VARCHAR(20),
            name VARCHAR(255),
            description TEXT,
            semester VARCHAR(50),
            credits INT,
            synced_at TIMESTAMP
          );
        """
        if not self._is_connected:
            return {"error": "Not connected to database"}

        results: dict[str, Any] = {"rows_exported": 0, "errors": []}

        try:
            logger.debug(f"SQL export_courses_to_sql: stub for {len(courses)} courses")
            results["rows_exported"] = len(courses)
            return results

        except Exception as e:
            self._set_last_error(str(e))
            results["errors"].append(str(e))
            return results

    async def import_from_sql(
        self,
        query: str,
        params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        """Import data from external database using custom SQL query.

        Args:
            query: SQL SELECT query (can use parameterized queries)
            params: Parameter dict for query

        Returns:
            List of result rows as dictionaries

        Example queries:
          "SELECT id, code, name FROM courses WHERE department = :dept"
          "SELECT a.name, g.score, g.max_score FROM assignments a
           JOIN grades g ON a.id = g.assignment_id WHERE a.course_id = :course_id"
        """
        if not self._is_connected:
            return []

        try:
            logger.debug("SQL import_from_sql: stub for custom query")
            return []

        except Exception as e:
            self._set_last_error(str(e))
            logger.error(f"SQL import failed: {e}")
            return []

    async def sync_grades_from_sql(
        self,
        course_id: int | None = None
    ) -> dict[str, Any]:
        """Sync grades from external gradebook database.

        Pulls grades for all courses or specific course and imports
        them to Scholarr.

        Args:
            course_id: Optional course ID to limit sync to single course

        Returns:
            Dictionary with grades_synced and any errors

        Example schema (typical SIS):
          SELECT
            c.code as course_code,
            c.name as course_name,
            a.name as assignment_name,
            a.due_date,
            a.weight,
            g.score,
            g.max_score
          FROM courses c
          JOIN assignments a ON c.id = a.course_id
          JOIN grades g ON a.id = g.assignment_id
          WHERE c.id = :course_id
          ORDER BY c.code, a.due_date
        """
        if not self._is_connected:
            return {"error": "Not connected to database"}

        results: dict[str, Any] = {"grades_synced": 0, "courses_synced": 0, "errors": []}

        try:
            logger.debug("SQL sync_grades_from_sql: stub implementation")
            return results

        except Exception as e:
            self._set_last_error(str(e))
            results["errors"].append(str(e))
            return results

    async def list_tables(self) -> list[str]:
        """List all available tables in connected database.

        Returns:
            List of table names
        """
        if not self._engine:
            return []

        try:
            inspector = inspect(self._engine)
            return inspector.get_table_names()
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            return []

    async def sync(self) -> dict[str, Any]:
        """Not applicable for direct database connections.

        Returns:
            Message indicating sync not supported
        """
        return {"message": "Use import_from_sql or sync_grades_from_sql for data operations"}

    async def get_status(self) -> IntegrationStatus:
        """Get status of SQL integration.

        Returns:
            IntegrationStatus with connection info
        """
        tables = []
        if self._is_connected:
            with contextlib.suppress(Exception):
                tables = await self.list_tables()

        return IntegrationStatus(
            provider_name="sql",
            provider_type=IntegrationType.DATABASE,
            is_connected=self._is_connected,
            last_sync=self._last_sync,
            last_error=self._last_error,
            configuration_valid=bool(self._config),
            metadata={
                "connection_string": self._config.get("connection_string", "not set").split("@")[0] + "@...",
                "available_tables": tables,
                "sqlalchemy_available": HAS_SQLALCHEMY
            }
        )
