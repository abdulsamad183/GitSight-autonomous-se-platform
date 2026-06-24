"""Add chunk source metadata, diff chunk types, and commit references."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

chunk_source = postgresql.ENUM(
    "symbol",
    "file",
    "section",
    "diff_hunk",
    name="chunk_source",
    create_type=False,
)
change_type = postgresql.ENUM(
    "add",
    "modify",
    "delete",
    name="change_type",
    create_type=False,
)


def upgrade() -> None:
    op.execute("ALTER TYPE chunk_type ADD VALUE IF NOT EXISTS 'file'")
    op.execute("ALTER TYPE chunk_type ADD VALUE IF NOT EXISTS 'section'")
    op.execute("ALTER TYPE chunk_type ADD VALUE IF NOT EXISTS 'diff_hunk'")

    chunk_source.create(op.get_bind(), checkfirst=True)
    change_type.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "code_chunks",
        sa.Column(
            "chunk_source",
            chunk_source,
            nullable=False,
            server_default="symbol",
        ),
    )
    op.add_column(
        "code_chunks",
        sa.Column("base_commit_hash", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "code_chunks",
        sa.Column("head_commit_hash", sa.String(length=40), nullable=True),
    )
    op.add_column(
        "code_chunks",
        sa.Column("change_type", change_type, nullable=True),
    )
    op.create_index(
        op.f("ix_code_chunks_head_commit_hash"),
        "code_chunks",
        ["head_commit_hash"],
        unique=False,
    )
    op.create_index(
        op.f("ix_code_chunks_base_commit_hash"),
        "code_chunks",
        ["base_commit_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_code_chunks_base_commit_hash"), table_name="code_chunks")
    op.drop_index(op.f("ix_code_chunks_head_commit_hash"), table_name="code_chunks")
    op.drop_column("code_chunks", "change_type")
    op.drop_column("code_chunks", "head_commit_hash")
    op.drop_column("code_chunks", "base_commit_hash")
    op.drop_column("code_chunks", "chunk_source")

    change_type.drop(op.get_bind(), checkfirst=True)
    chunk_source.drop(op.get_bind(), checkfirst=True)
