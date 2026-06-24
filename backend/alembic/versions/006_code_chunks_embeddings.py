"""Code chunks, chunk embeddings (pgvector), and repository indexing status."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

chunk_type = postgresql.ENUM(
    "function",
    "method",
    "class",
    "interface",
    "enum",
    "module",
    name="chunk_type",
    create_type=False,
)
indexing_status = postgresql.ENUM(
    "pending",
    "processing",
    "completed",
    "failed",
    name="indexing_status",
    create_type=False,
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.execute("ALTER TYPE symbol_type ADD VALUE IF NOT EXISTS 'interface'")
    op.execute("ALTER TYPE symbol_type ADD VALUE IF NOT EXISTS 'enum'")

    indexing_status.create(op.get_bind(), checkfirst=True)
    chunk_type.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "repositories",
        sa.Column(
            "indexing_status",
            indexing_status,
            nullable=False,
            server_default="pending",
        ),
    )
    op.add_column(
        "repositories",
        sa.Column("total_chunks", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "repositories",
        sa.Column("embedded_chunks", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "repositories",
        sa.Column("indexing_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "repositories",
        sa.Column("indexing_completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "repositories",
        sa.Column("indexing_duration_seconds", sa.Float(), nullable=True),
    )

    op.create_table(
        "code_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("branch_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("chunk_type", chunk_type, nullable=False),
        sa.Column("symbol_name", sa.String(length=512), nullable=False),
        sa.Column("parent_symbol", sa.String(length=512), nullable=True),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["repository_id"], ["repositories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "repository_id",
            "branch_name",
            "file_path",
            "symbol_name",
            "chunk_type",
            "start_line",
            name="uq_code_chunks_symbol_location",
        ),
    )
    op.create_index(
        op.f("ix_code_chunks_repository_id"),
        "code_chunks",
        ["repository_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_code_chunks_branch_name"),
        "code_chunks",
        ["branch_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_code_chunks_file_path"),
        "code_chunks",
        ["file_path"],
        unique=False,
    )
    op.create_index(
        "ix_code_chunks_repo_branch_file",
        "code_chunks",
        ["repository_id", "branch_name", "file_path"],
        unique=False,
    )
    op.create_index(
        "ix_code_chunks_repo_content_hash",
        "code_chunks",
        ["repository_id", "content_hash"],
        unique=False,
    )

    op.create_table(
        "chunk_embeddings",
        sa.Column("chunk_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["chunk_id"], ["code_chunks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("chunk_id"),
    )


def downgrade() -> None:
    op.drop_table("chunk_embeddings")
    op.drop_index("ix_code_chunks_repo_content_hash", table_name="code_chunks")
    op.drop_index("ix_code_chunks_repo_branch_file", table_name="code_chunks")
    op.drop_index(op.f("ix_code_chunks_file_path"), table_name="code_chunks")
    op.drop_index(op.f("ix_code_chunks_branch_name"), table_name="code_chunks")
    op.drop_index(op.f("ix_code_chunks_repository_id"), table_name="code_chunks")
    op.drop_table("code_chunks")

    op.drop_column("repositories", "indexing_duration_seconds")
    op.drop_column("repositories", "indexing_completed_at")
    op.drop_column("repositories", "indexing_started_at")
    op.drop_column("repositories", "embedded_chunks")
    op.drop_column("repositories", "total_chunks")
    op.drop_column("repositories", "indexing_status")

    chunk_type.drop(op.get_bind(), checkfirst=True)
    indexing_status.drop(op.get_bind(), checkfirst=True)
