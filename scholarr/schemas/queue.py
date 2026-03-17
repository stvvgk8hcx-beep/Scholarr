"""Queue status schemas."""

from pydantic import BaseModel


class QueueStatusResponse(BaseModel):
    """Schema for queue status response."""

    pending_count: int
    processing_count: int
    completed_count: int
    failed_count: int
    total_count: int
