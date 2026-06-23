import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, enum_values


class SymbolType(str, enum.Enum):
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"


class Symbol(BaseModel):
    __tablename__ = "symbols"

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
    file_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("files.id", ondelete="CASCADE"),
        index=True,
    )
    symbol_name: Mapped[str] = mapped_column(String(512), nullable=False)
    symbol_type: Mapped[SymbolType] = mapped_column(
        Enum(SymbolType, name="symbol_type", values_callable=enum_values),
        nullable=False,
    )
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)

    file = relationship("File", back_populates="symbols")
