"""Import result schemas."""

from typing import Optional, List
from pydantic import BaseModel


class ImportResultResponse(BaseModel):
    """Schema for import operation result."""

    success: bool
    message: str
    imported_count: int = 0
    failed_count: int = 0
    errors: List[str] = []
    file_id: Optional[int] = None
