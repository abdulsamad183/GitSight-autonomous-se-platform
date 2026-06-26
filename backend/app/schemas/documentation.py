from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DocumentationTypeItem(BaseModel):
    document_type: str
    title: str
    available: bool
    generated_by: str | None = None
    generated_at: datetime | None = None
    source_path: str | None = None


class DocumentationListResponse(BaseModel):
    types: list[DocumentationTypeItem]


class DocumentationResponse(BaseModel):
    document_type: str
    title: str
    content: str
    generated_by: str
    generated_at: datetime
    source_path: str | None = None
