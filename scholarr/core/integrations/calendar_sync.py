"""Calendar integration for syncing due dates and deadlines.

Exports Scholarr academic items as calendar events.
Supports iCalendar (ICS) format for universal calendar compatibility.
Stub implementations for Google Calendar and Outlook Calendar sync.
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from scholarr.core.integrations import BaseIntegrationProvider, IntegrationStatus, IntegrationType

logger = logging.getLogger(__name__)


class CalendarSyncProvider(BaseIntegrationProvider):
    """Calendar integration provider.

    Exports due dates to calendar formats and syncs with calendar services.
    """

    def __init__(self):
        """Initialize calendar sync provider."""
        super().__init__("calendar_sync", IntegrationType.CALENDAR)

    async def connect(self, config: dict[str, Any]) -> bool:
        """Connect to calendar service (optional).

        Config can contain calendar service credentials.

        Args:
            config: Configuration dictionary

        Returns:
            True (calendar export doesn't require active connection)
        """
        self._is_connected = True
        self._clear_last_error()
        return True

    async def disconnect(self) -> bool:
        """Disconnect from calendar service.

        Returns:
            True
        """
        self._is_connected = False
        return True

    async def sync(self) -> dict[str, Any]:
        """Not applicable for calendar export.

        Returns:
            Message
        """
        return {"message": "Use generate_ics or sync_to_google_calendar instead"}

    async def test_connection(self) -> bool:
        """Calendar provider always works.

        Returns:
            True
        """
        return True

    def generate_ics(self, academic_items: list[dict[str, Any]]) -> str:
        """Generate iCalendar format (.ics) from academic items.

        Creates VEVENT entries for each item with a due date.
        iCalendar is widely supported by calendar applications (Google Calendar,
        Outlook, Apple Calendar, etc.).

        Args:
            academic_items: List of academic item dicts with at least:
                - name/title
                - due_date (datetime or ISO string)
                - course_code or course_name (optional, for description)
                - description (optional)

        Returns:
            Complete iCalendar file content as string
        """
        try:
            # iCalendar format specification: RFC 5545
            # This is the actual implementation (not a stub)

            lines = [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//Scholarr//v0.1.0//EN",
                "CALSCALE:GREGORIAN",
                "METHOD:PUBLISH",
                "X-WR-CALNAME:Scholarr Academic Calendar",
                "X-WR-TIMEZONE:UTC",
                "X-WR-CALDESC:Academic due dates and deadlines from Scholarr",
                "BEGIN:VTIMEZONE",
                "TZID:UTC",
                "BEGIN:STANDARD",
                "DTSTART:19700101T000000Z",
                "TZOFFSETFROM:+0000",
                "TZOFFSETTO:+0000",
                "END:STANDARD",
                "END:VTIMEZONE",
            ]

            for item in academic_items:
                # Skip items without due dates
                due_date = item.get("due_date") or item.get("dueDate")
                if not due_date:
                    continue

                # Parse due date
                if isinstance(due_date, str):
                    # Try to parse ISO format or common formats
                    try:
                        due_dt = datetime.fromisoformat(due_date.replace("Z", "+00:00"))
                    except ValueError:
                        logger.warning(f"Could not parse due date: {due_date}")
                        continue
                elif isinstance(due_date, datetime):
                    due_dt = due_date
                else:
                    continue

                # Build event
                event_lines = [
                    "BEGIN:VEVENT",
                    f"UID:{uuid.uuid4()}@scholarr",
                    f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}",
                    f"DTSTART:{due_dt.strftime('%Y%m%dT%H%M%SZ')}",
                ]

                # Use name/title
                title = item.get("name") or item.get("title") or "Untitled"
                # Escape special characters in iCal format
                title = self._escape_ical_text(title)
                event_lines.append(f"SUMMARY:{title}")

                # Build description from course code and item details
                desc_parts = []
                if item.get("course_code"):
                    desc_parts.append(f"Course: {item['course_code']}")
                if item.get("course_name"):
                    desc_parts.append(f"Course: {item['course_name']}")
                if item.get("description"):
                    desc_parts.append(item["description"])

                if desc_parts:
                    description = "\n".join(desc_parts)
                    description = self._escape_ical_text(description)
                    event_lines.append(f"DESCRIPTION:{description}")

                # Add course as location if available
                if item.get("course_code"):
                    location = self._escape_ical_text(item["course_code"])
                    event_lines.append(f"LOCATION:{location}")

                # Add alarm (30 minutes before)
                event_lines.extend([
                    "BEGIN:VALARM",
                    "TRIGGER:-PT30M",
                    "ACTION:DISPLAY",
                    f"DESCRIPTION:Reminder: {title}",
                    "END:VALARM",
                ])

                event_lines.append("END:VEVENT")
                lines.extend(event_lines)

            lines.append("END:VCALENDAR")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Failed to generate iCalendar: {e}")
            return ""

    def _escape_ical_text(self, text: str) -> str:
        """Escape special characters for iCalendar format.

        Args:
            text: Text to escape

        Returns:
            Escaped text safe for iCalendar
        """
        # iCalendar escaping: backslash escapes for \, ;, ,, and newline becomes \n
        text = text.replace("\\", "\\\\")
        text = text.replace(";", "\\;")
        text = text.replace(",", "\\,")
        text = text.replace("\n", "\\n")
        return text

    async def sync_to_google_calendar(
        self,
        academic_items: list[dict[str, Any]],
        google_service: Any | None = None
    ) -> dict[str, Any]:
        """Sync academic items to Google Calendar.

        Requires Google Calendar API service object.

        Args:
            academic_items: List of academic items
            google_service: Google API service object (optional, would be injected)

        Returns:
            Dictionary with events_created and any errors
        """
        logger.debug("sync_to_google_calendar: stub implementation")
        return {"events_created": 0}

    async def sync_to_outlook_calendar(
        self,
        academic_items: list[dict[str, Any]],
        outlook_service: Any | None = None
    ) -> dict[str, Any]:
        """Sync academic items to Outlook/Microsoft 365 Calendar.

        Requires Microsoft Graph API service or client.

        Args:
            academic_items: List of academic items
            outlook_service: Microsoft Graph service object (optional)

        Returns:
            Dictionary with events_created and any errors
        """
        logger.debug("sync_to_outlook_calendar: stub implementation")
        return {"events_created": 0}

    async def get_status(self) -> IntegrationStatus:
        """Get status of calendar sync provider.

        Returns:
            IntegrationStatus
        """
        return IntegrationStatus(
            provider_name="calendar_sync",
            provider_type=IntegrationType.CALENDAR,
            is_connected=self._is_connected,
            last_sync=self._last_sync,
            last_error=self._last_error,
            configuration_valid=True,
            metadata={
                "capabilities": [
                    "generate_ics",
                    "sync_to_google_calendar",
                    "sync_to_outlook_calendar"
                ],
                "ical_generation": "fully_implemented",
                "calendar_service_sync": "stub_for_future_impl"
            }
        )
