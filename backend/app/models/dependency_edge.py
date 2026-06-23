import enum
import uuid

from sqlalchemy import Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, enum_values


class DependencyType(str, enum.Enum):
    IMPORT = "IMPORT"
    FROM_IMPORT = "FROM_IMPORT"
    REQUIRE = "REQUIRE"
    INCLUDE = "INCLUDE"


class DependencyEdge(BaseModel):
    __tablename__ = "dependency_edges"

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
    source_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        index=True,
    )
    target_file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        index=True,
    )
    dependency_type: Mapped[DependencyType] = mapped_column(
        Enum(DependencyType, name="dependency_type", values_callable=enum_values),
        nullable=False,
    )

    source_file = relationship(
        "File",
        back_populates="outgoing_edges",
        foreign_keys=[source_file_id],
    )
    target_file = relationship(
        "File",
        back_populates="incoming_edges",
        foreign_keys=[target_file_id],
    )
