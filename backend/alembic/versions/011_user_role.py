"""Add users.role and enforce a single admin."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011"
down_revision: Union[str, None] = "010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("role", sa.String(length=32), server_default="user", nullable=False),
    )
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)
    op.create_index(
        "uq_users_one_admin",
        "users",
        ["role"],
        unique=True,
        postgresql_where=sa.text("role = 'admin'"),
    )


def downgrade() -> None:
    op.drop_index("uq_users_one_admin", table_name="users")
    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_column("users", "role")
