"""Calendar endpoint."""

from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.calendar import CalendarDayResponse
from scholarr.services.calendar_service import CalendarService

router = APIRouter()


@router.get("", response_model=list[CalendarDayResponse])
async def get_calendar_entries(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get due dates for a date range."""
    service = CalendarService(db)
    entries = await service.get_calendar_entries(start_date=start_date, end_date=end_date)
    return entries
