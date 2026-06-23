import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class File(BaseModel):
    __tablename__ = "files"
    __table_args__ = (Index("ix_files_snapshot_relative_path", "snapshot_id", "relative_path"),)

    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repositories.id", ondelete="CASCADE"),
        index=True,
    )
    snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("repository_snapshots.id", ondelete="CASCADE"),
        index=True,
    )
    relative_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    extension: Mapped[str | None] = mapped_column(String(32), nullable=True)
    language: Mapped[str | None] = mapped_column(String(32), nullable=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    is_binary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    repository = relationship("Repository", back_populates="files")
    snapshot = relationship("RepositorySnapshot", back_populates="files")
    symbols = relationship(
        "Symbol",
        back_populates="file",
        cascade="all, delete-orphan",
    )
    outgoing_edges = relationship(
        "DependencyEdge",
        back_populates="source_file",
        foreign_keys="DependencyEdge.source_file_id",
        cascade="all, delete-orphan",
    )
    incoming_edges = relationship(
        "DependencyEdge",
        back_populates="target_file",
        foreign_keys="DependencyEdge.target_file_id",
        cascade="all, delete-orphan",
    )
