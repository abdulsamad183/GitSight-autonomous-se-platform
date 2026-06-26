from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PullRequestReviewResponse(BaseModel):
    pull_request_id: UUID
    title: str
    content: str
    generated_at: datetime
