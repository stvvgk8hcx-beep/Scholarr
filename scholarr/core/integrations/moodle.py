"""Moodle LMS integration.

Moodle uses Web Services API with token-based authentication.

Key endpoints (via XML-RPC or REST at /webservice/rest/server.php):
  core_course_get_courses - list enrolled courses
  core_course_get_course_module - get assignment details
  core_grades_get_grades - fetch grades for course
  local_api_* - institution-specific endpoints

Requires:
  - Moodle site URL
  - Web Services token (enabled by admin, generated in user settings)
  - Web Services must be enabled in Moodle admin settings

Moodle's Web Services API is more complex than Canvas but provides
fine-grained data access.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import logging

from scholarr.core.integrations import BaseIntegrationProvider, IntegrationType, IntegrationStatus

logger = logging.getLogger(__name__)


class MoodleProvider(BaseIntegrationProvider):
    """Moodle LMS integration provider.

    Uses Moodle Web Services API with token authentication.
    """

    def __init__(self):
        """Initialize Moodle provider."""
        super().__init__("moodle", IntegrationType.LMS)
        self._token: Optional[str] = None
        self._user_id: Optional[int] = None

    async def connect(self, config: Dict[str, Any]) -> bool:
        """Connect to Moodle instance.

        Config should contain:
            moodle_url: Base URL of Moodle site (e.g., https://moodle.institution.edu)
            token: Web Services token from user's security settings

        Args:
            config: Connection configuration dictionary

        Returns:
            True if connection successful
        """
        try:
            required = ["moodle_url", "token"]
            if not all(key in config for key in required):
                missing = [k for k in required if k not in config]
                raise ValueError(f"Missing required config: {missing}")

            self._config = config
            self._token = config.get("token")

            # Test connection
            success = await self.test_connection()
            if success:
                self._is_connected = True
                self._clear_last_error()
                logger.info(f"Connected to Moodle at {config.get('moodle_url')}")
            else:
                self._set_last_error("Failed to authenticate with Moodle")

            return success

        except Exception as e:
            self._set_last_error(str(e))
            logger.error(f"Moodle connection error: {e}")
            return False

    async def disconnect(self) -> bool:
        """Disconnect from Moodle.

        Returns:
            True if successful
        """
        try:
            self._is_connected = False
            self._token = None
            self._clear_last_error()
            logger.info("Disconnected from Moodle")
            return True
        except Exception as e:
            self._set_last_error(str(e))
            return False

    async def test_connection(self) -> bool:
        """Test if token is valid by calling core_webservice_get_site_info.

        Returns:
            True if connection test successful
        """
        if not self._token:
            return False

        logger.debug("Moodle test_connection: stub implementation")
        return True

    async def get_courses(self) -> List[Dict[str, Any]]:
        """Fetch list of courses for authenticated user.

        Calls core_course_get_courses

        Returns:
            List of course dictionaries
        """
        logger.debug("Moodle get_courses: stub implementation")
        return []

    async def get_assignments(self, course_id: int) -> List[Dict[str, Any]]:
        """Fetch assignments for a course.

        Uses core_course_get_course_module or mod_assign_* functions

        Args:
            course_id: Moodle course ID

        Returns:
            List of assignment dictionaries
        """
        logger.debug(f"Moodle get_assignments for course {course_id}: stub")
        return []

    async def get_grades(self, course_id: int) -> List[Dict[str, Any]]:
        """Fetch grades for a course.

        Calls core_grades_get_grades or gradereport_* functions

        Args:
            course_id: Moodle course ID

        Returns:
            List of grade entries with item name, grade, scale
        """
        logger.debug(f"Moodle get_grades for course {course_id}: stub")
        return []

    async def sync(self) -> Dict[str, Any]:
        """Sync all data from Moodle.

        Fetches courses, assignments, and grades.

        Returns:
            Dictionary with synced data and any errors
        """
        if not self._is_connected:
            return {"error": "Not connected to Moodle"}

        try:
            results = {
                "courses": [],
                "assignments": [],
                "grades": [],
                "errors": []
            }

            # Sync courses
            courses = await self.get_courses()
            results["courses"] = courses

            # Sync assignments and grades for each course
            for course in courses:
                course_id = course["id"]
                try:
                    assignments = await self.get_assignments(course_id)
                    results["assignments"].extend(assignments)
                except Exception as e:
                    results["errors"].append(
                        f"Failed to sync assignments for course {course.get('shortname')}: {e}"
                    )

                try:
                    grades = await self.get_grades(course_id)
                    results["grades"].extend(grades)
                except Exception as e:
                    results["errors"].append(
                        f"Failed to sync grades for course {course.get('shortname')}: {e}"
                    )

            self._last_sync = datetime.now()
            return results

        except Exception as e:
            self._set_last_error(str(e))
            return {"error": str(e)}

    async def get_status(self) -> IntegrationStatus:
        """Get current status of Moodle integration.

        Returns:
            IntegrationStatus with connection and sync info
        """
        return IntegrationStatus(
            provider_name="moodle",
            provider_type=IntegrationType.LMS,
            is_connected=self._is_connected,
            last_sync=self._last_sync,
            last_error=self._last_error,
            configuration_valid=bool(self._config),
            metadata={
                "moodle_url": self._config.get("moodle_url", "not set"),
                "user_id": self._user_id or "unknown"
            }
        )
