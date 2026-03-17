"""File System schemas."""

from datetime import datetime
from pydantic import BaseModel


class DirectoryEntryResponse(BaseModel):
    """Schema for a file system directory entry."""

    name: str
    path: str
    is_directory: bool
    size: int
    modified_at: datetime
    created_at: datetime
