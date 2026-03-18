"""Commands endpoint."""


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.command import CommandCreate, CommandResponse
from scholarr.services.command_service import CommandService

router = APIRouter()


@router.get("", response_model=list[CommandResponse])
async def list_commands(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """List queued commands."""
    service = CommandService(db)
    commands = await service.list_commands(status=status, limit=limit)
    return commands


@router.get("/{id}", response_model=CommandResponse)
async def get_command(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get a command by ID."""
    service = CommandService(db)
    command = await service.get_command(id)
    if not command:
        raise HTTPException(status_code=404, detail="Command not found")
    return command


@router.post("", response_model=CommandResponse, status_code=201)
async def queue_command(
    command: CommandCreate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Queue a new command for processing."""
    service = CommandService(db)
    new_command = await service.queue_command(command)
    return new_command
