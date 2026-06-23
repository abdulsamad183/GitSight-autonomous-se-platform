from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class JobEventItem(BaseModel):
    message: str
    created_at: datetime


class JobStatusResponse(BaseModel):
    id: UUID
    status: str
    progress: int
    current_stage: str | None
    error_message: str | None
    events: list[JobEventItem] = []
