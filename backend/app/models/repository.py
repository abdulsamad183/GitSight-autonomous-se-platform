import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, enum_values


class RepositoryStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    FAILED = "failed"
    ARCHIVED = "archived"


class Repository(BaseModel):
    __tablename__ = "repositories"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255))
    repo_url: Mapped[str] = mapped_column(String(512))
    owner: Mapped[str] = mapped_column(String(255))
    repository_name: Mapped[str] = mapped_column(String(255))
    default_branch: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latest_commit_hash: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    branches_analyzed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    branches_truncated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[RepositoryStatus] = mapped_column(
        Enum(RepositoryStatus, name="repository_status", values_callable=enum_values),
        default=RepositoryStatus.PENDING,
        nullable=False,
    )

    user = relationship("User", back_populates="repositories")
    jobs = relationship(
        "Job",
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    snapshots = relationship(
        "RepositorySnapshot",
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    files = relationship(
        "File",
        back_populates="repository",
        cascade="all, delete-orphan",
    )
    pull_requests = relationship(
        "PullRequest",
        back_populates="repository",
        cascade="all, delete-orphan",
    )
