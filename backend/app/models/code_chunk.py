import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, enum_values


class ChunkType(str, enum.Enum):
    FUNCTION = "function"
    METHOD = "method"
    CLASS = "class"
    INTERFACE = "interface"
    ENUM = "enum"
    MODULE = "module"
    FILE = "file"
    SECTION = "section"
    DIFF_HUNK = "diff_hunk"


class ChunkSource(str, enum.Enum):
    SYMBOL = "symbol"
    FILE = "file"
    SECTION = "section"
    DIFF_HUNK = "diff_hunk"


class ChangeType(str, enum.Enum):
    ADD = "add"
    MODIFY = "modify"
    DELETE = "delete"


class CodeChunk(BaseModel):
    __tablename__ = "code_chunks"
    __table_args__ = (
        UniqueConstraint(
            "repository_id",
            "branch_name",
            "file_path",
            "symbol_name",
            "chunk_type",
            "start_line",
            name="uq_code_chunks_symbol_location",
        ),
        Index("ix_code_chunks_repo_branch_file", "repository_id", "branch_name", "file_path"),
        Index("ix_code_chunks_repo_content_hash", "repository_id", "content_hash"),
    )

    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        index=True,
    )
    branch_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False, index=True)
    chunk_type: Mapped[ChunkType] = mapped_column(
        Enum(ChunkType, name="chunk_type", values_callable=enum_values),
        nullable=False,
    )
    symbol_name: Mapped[str] = mapped_column(String(512), nullable=False)
    parent_symbol: Mapped[str | None] = mapped_column(String(512), nullable=True)
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    chunk_source: Mapped[ChunkSource] = mapped_column(
        Enum(ChunkSource, name="chunk_source", values_callable=enum_values),
        nullable=False,
        default=ChunkSource.SYMBOL,
    )
    base_commit_hash: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    head_commit_hash: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    change_type: Mapped[ChangeType | None] = mapped_column(
        Enum(ChangeType, name="change_type", values_callable=enum_values),
        nullable=True,
    )

    repository = relationship("Repository", back_populates="code_chunks")
    embedding = relationship(
        "ChunkEmbedding",
        back_populates="chunk",
        uselist=False,
        cascade="all, delete-orphan",
    )
