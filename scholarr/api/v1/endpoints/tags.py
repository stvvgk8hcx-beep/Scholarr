"""Tags endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from scholarr.core.security import verify_api_key
from scholarr.db.session import get_db_session
from scholarr.schemas.tag import TagCreate, TagResponse, TagUpdate
from scholarr.services.tag_service import TagService

router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def list_tags(
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """List all tags."""
    service = TagService(db)
    tags = await service.list_tags()
    return tags


@router.get("/{id}", response_model=TagResponse)
async def get_tag(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Get a tag by ID."""
    service = TagService(db)
    tag = await service.get_tag(id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.post("", response_model=TagResponse, status_code=201)
async def create_tag(
    tag: TagCreate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Create a new tag."""
    service = TagService(db)
    try:
        new_tag = await service.create_tag(tag)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from None
    return new_tag


@router.put("/{id}", response_model=TagResponse)
async def update_tag(
    id: int,
    tag_update: TagUpdate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Update a tag."""
    service = TagService(db)
    updated = await service.update_tag(id, tag_update)
    if not updated:
        raise HTTPException(status_code=404, detail="Tag not found")
    return updated


@router.delete("/{id}", status_code=204)
async def delete_tag(
    id: int,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key),
):
    """Delete a tag."""
    service = TagService(db)
    success = await service.delete_tag(id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return None
