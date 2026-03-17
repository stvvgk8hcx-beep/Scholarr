"""File System schemas."""

from typing import Optional

from pydantic import BaseModel


class DirectoryEntryResponse(BaseModel):
    """Schema for a file system directory entry."""

    name: str
    path: str
    is_dir: bool
    size: Optional[int] = None
    modified: str
    created_at: Optional[str] = None
