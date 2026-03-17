"""Integration management API endpoints.

Provides HTTP endpoints for managing external integrations:
  - List available and active integrations
  - Connect/disconnect from providers
  - Trigger sync operations
  - Extract metadata from files
  - Export to calendar format
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.core.integrations import (
    get_registry,
    IntegrationRegistry,
    IntegrationStatus,
    IntegrationType
)
from scholarr.core.integrations.word_integration import WordIntegrationProvider
from scholarr.core.integrations.calendar_sync import CalendarSyncProvider

router = APIRouter()


@router.get("")
async def list_integrations(
    api_key: str = Depends(verify_api_key),
) -> dict:
    """List available and active integrations.

    Returns info about all registered providers and their status.
    """
    registry = get_registry()

    return {
        "available_providers": registry.list_available_providers(),
        "active_providers": registry.list_active_providers(),
        "integration_types": [t.value for t in IntegrationType]
    }


@router.get("/status")
async def get_all_statuses(
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Get status for all active integrations."""
    registry = get_registry()
    statuses = await registry.get_all_statuses()

    return {
        "statuses": {
            name: {
                "provider_name": status.provider_name,
                "provider_type": status.provider_type.value,
                "is_connected": status.is_connected,
                "last_sync": status.last_sync.isoformat() if status.last_sync else None,
                "last_error": status.last_error,
                "configuration_valid": status.configuration_valid,
                "metadata": status.metadata
            }
            for name, status in statuses.items()
        }
    }


@router.post("/{provider}/connect")
async def connect_provider(
    provider: str,
    config: dict,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Connect to a specific integration provider.

    Args:
        provider: Provider name (blackboard, canvas, moodle, word, sql, etc.)
        config: Provider-specific configuration dictionary

    Returns:
        Status of connection attempt
    """
    registry = get_registry()

    # Get the provider class
    provider_class = registry.get_available_provider_class(provider)
    if not provider_class:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not available")

    try:
        # Instantiate and connect
        instance = provider_class()
        success = await instance.connect(config)

        if success:
            registry.register_active(provider, instance)
            return {
                "status": "connected",
                "provider": provider,
                "message": f"Successfully connected to {provider}"
            }
        else:
            return {
                "status": "failed",
                "provider": provider,
                "error": instance._last_error or "Connection failed"
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection error: {str(e)}")


@router.post("/{provider}/disconnect")
async def disconnect_provider(
    provider: str,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Disconnect from a specific integration provider.

    Args:
        provider: Provider name to disconnect

    Returns:
        Status of disconnection
    """
    registry = get_registry()
    instance = registry.get_provider(provider)

    if not instance:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not connected")

    try:
        success = await instance.disconnect()
        if success:
            return {
                "status": "disconnected",
                "provider": provider,
                "message": f"Successfully disconnected from {provider}"
            }
        else:
            return {
                "status": "failed",
                "provider": provider,
                "error": "Disconnection failed"
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Disconnection error: {str(e)}")


@router.post("/{provider}/sync")
async def trigger_sync(
    provider: str,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Trigger sync for a specific provider.

    Fetches latest data from the external service.

    Args:
        provider: Provider name to sync from

    Returns:
        Sync results with counts and errors
    """
    registry = get_registry()
    instance = registry.get_provider(provider)

    if not instance:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not connected")

    try:
        results = await instance.sync()
        return {
            "status": "synced",
            "provider": provider,
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Sync error: {str(e)}")


@router.get("/{provider}/status")
async def get_provider_status(
    provider: str,
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Get status for a specific provider.

    Args:
        provider: Provider name

    Returns:
        Detailed status information
    """
    registry = get_registry()
    instance = registry.get_provider(provider)

    if not instance:
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found")

    try:
        status = await instance.get_status()
        return {
            "provider": provider,
            "status": {
                "is_connected": status.is_connected,
                "last_sync": status.last_sync.isoformat() if status.last_sync else None,
                "last_error": status.last_error,
                "configuration_valid": status.configuration_valid,
                "metadata": status.metadata
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Status check error: {str(e)}")


@router.post("/word/extract")
async def extract_from_word(
    file: UploadFile = File(...),
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Extract metadata and info from uploaded Word document.

    Supports .docx files. Extracts:
      - Document metadata (title, author, created date, etc.)
      - Heading structure
      - Tables
      - Detected assignment information (course code, due date, etc.)

    Args:
        file: Uploaded Word document (.docx)

    Returns:
        Extracted data dictionary
    """
    if not file.filename.endswith(".docx"):
        raise HTTPException(status_code=400, detail="File must be .docx format")

    try:
        # Save uploaded file temporarily
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            provider = WordIntegrationProvider()

            # Extract all available data
            metadata = provider.extract_metadata(tmp_path)
            headings = provider.extract_headings(tmp_path)
            tables = provider.extract_tables(tmp_path)
            assignment_info = provider.detect_assignment_info(tmp_path)

            return {
                "file": file.filename,
                "metadata": metadata,
                "headings": headings,
                "tables": tables,
                "assignment_info": assignment_info
            }

        finally:
            os.unlink(tmp_path)

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Extraction error: {str(e)}")


@router.post("/calendar/generate-ics")
async def generate_calendar_ics(
    academic_items: List[dict],
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Generate iCalendar (.ics) file from academic items.

    Can be imported into Google Calendar, Outlook, Apple Calendar, etc.

    Args:
        academic_items: List of academic items with due dates

    Returns:
        iCalendar content and info
    """
    try:
        provider = CalendarSyncProvider()
        ics_content = provider.generate_ics(academic_items)

        if not ics_content:
            raise HTTPException(status_code=400, detail="Failed to generate iCalendar")

        return {
            "status": "generated",
            "format": "iCalendar (RFC 5545)",
            "items_included": len(academic_items),
            "content": ics_content,
            "filename": "scholarr-calendar.ics"
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Generation error: {str(e)}")


@router.post("/calendar/export")
async def export_to_calendar(
    academic_items: List[dict],
    calendar_service: str = Query("ics", pattern="^(ics|google|outlook)$"),
    api_key: str = Depends(verify_api_key),
) -> dict:
    """Export academic items to calendar.

    Supports:
      - ics: Generate iCalendar file (use separately with calendar apps)
      - google: Sync to Google Calendar (requires oauth_token in config)
      - outlook: Sync to Outlook/Microsoft 365 (requires credentials in config)

    Args:
        academic_items: List of academic items
        calendar_service: Calendar service to export to (ics, google, outlook)

    Returns:
        Export results
    """
    try:
        provider = CalendarSyncProvider()

        if calendar_service == "ics":
            ics_content = provider.generate_ics(academic_items)
            return {
                "status": "exported",
                "service": "iCalendar",
                "filename": "scholarr-calendar.ics",
                "content": ics_content
            }

        elif calendar_service == "google":
            results = await provider.sync_to_google_calendar(academic_items)
            return {
                "status": "exported" if results.get("events_created", 0) > 0 else "pending",
                "service": "Google Calendar",
                "results": results
            }

        elif calendar_service == "outlook":
            results = await provider.sync_to_outlook_calendar(academic_items)
            return {
                "status": "exported" if results.get("events_created", 0) > 0 else "pending",
                "service": "Outlook Calendar",
                "results": results
            }

        else:
            raise HTTPException(status_code=400, detail="Unknown calendar service")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Export error: {str(e)}")
