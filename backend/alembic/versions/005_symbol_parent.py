"""Add parent_symbol_id to symbols for class-method hierarchy."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "symbols",
        sa.Column("parent_symbol_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_symbols_parent_symbol_id",
        "symbols",
        "symbols",
        ["parent_symbol_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        op.f("ix_symbols_parent_symbol_id"),
        "symbols",
        ["parent_symbol_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_symbols_parent_symbol_id"), table_name="symbols")
    op.drop_constraint("fk_symbols_parent_symbol_id", "symbols", type_="foreignkey")
    op.drop_column("symbols", "parent_symbol_id")
