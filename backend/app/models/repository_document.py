import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, enum_values


class DocumentType(str, enum.Enum):
    REPOSITORY_OVERVIEW = "repository_overview"
    ARCHITECTURE_OVERVIEW = "architecture_overview"
    MODULES = "modules"
    CLASSES = "classes"
    FUNCTIONS = "functions"
    BRANCH_SUMMARY = "branch_summary"


class DocumentGeneratedBy(str, enum.Enum):
    REPOSITORY = "repository"
    AI = "ai"


DOCUMENT_TYPE_TITLES: dict[DocumentType, str] = {
    DocumentType.REPOSITORY_OVERVIEW: "Repository Overview",
    DocumentType.ARCHITECTURE_OVERVIEW: "Architecture Overview",
    DocumentType.MODULES: "Modules",
    DocumentType.CLASSES: "Classes",
    DocumentType.FUNCTIONS: "Functions",
    DocumentType.BRANCH_SUMMARY: "Branch Summary",
}


class RepositoryDocument(BaseModel):
    __tablename__ = "repository_documents"
    __table_args__ = (
        UniqueConstraint("repository_id", "document_type", name="uq_repository_documents_type"),
    )

    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        index=True,
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, name="document_type", values_callable=enum_values),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    generated_by: Mapped[DocumentGeneratedBy] = mapped_column(
        Enum(DocumentGeneratedBy, name="document_generated_by", values_callable=enum_values),
        nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    source_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    repository = relationship("Repository", back_populates="documents")
