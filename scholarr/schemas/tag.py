"""Tag schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TagCreate(BaseModel):
    label: str = Field(min_length=1, max_length=100)
    color: str | None = None


class TagUpdate(BaseModel):
    label: str | None = None
    color: str | None = None


class TagResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    label: str
    color: str | None
    created_at: datetime
    updated_at: datetime
