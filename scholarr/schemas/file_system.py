"""File System schemas."""


from pydantic import BaseModel


class DirectoryEntryResponse(BaseModel):
    """Schema for a file system directory entry."""

    name: str
    path: str
    is_dir: bool
    size: int | None = None
    modified: str
    created_at: str | None = None
