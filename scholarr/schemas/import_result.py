"""Import result schemas."""


from pydantic import BaseModel


class ImportResultResponse(BaseModel):
    """Schema for import operation result."""

    success: bool
    message: str
    imported_count: int = 0
    failed_count: int = 0
    errors: list[str] = []
    file_id: int | None = None
