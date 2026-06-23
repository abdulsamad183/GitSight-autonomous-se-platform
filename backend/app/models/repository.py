import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


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
    status: Mapped[RepositoryStatus] = mapped_column(
        Enum(RepositoryStatus, name="repository_status"),
        default=RepositoryStatus.PENDING,
        nullable=False,
    )

    user = relationship("User", back_populates="repositories")
    jobs = relationship(
        "Job",
        back_populates="repository",
        cascade="all, delete-orphan",
    )
