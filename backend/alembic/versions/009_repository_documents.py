"""Add repository_documents table for cached documentation."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009"
down_revision: Union[str, None] = "008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

document_type = postgresql.ENUM(
    "repository_overview",
    "architecture_overview",
    "modules",
    "classes",
    "functions",
    "branch_summary",
    name="document_type",
    create_type=False,
)
document_generated_by = postgresql.ENUM(
    "repository",
    "ai",
    name="document_generated_by",
    create_type=False,
)


def upgrade() -> None:
    document_type.create(op.get_bind(), checkfirst=True)
    document_generated_by.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "repository_documents",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("repository_id", sa.UUID(), nullable=False),
        sa.Column("document_type", document_type, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("generated_by", document_generated_by, nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("source_path", sa.String(length=1024), nullable=True),
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
        sa.UniqueConstraint("repository_id", "document_type", name="uq_repository_documents_type"),
    )
    op.create_index(
        "ix_repository_documents_repository_id",
        "repository_documents",
        ["repository_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_repository_documents_repository_id", table_name="repository_documents")
    op.drop_table("repository_documents")
    document_generated_by.drop(op.get_bind(), checkfirst=True)
    document_type.drop(op.get_bind(), checkfirst=True)
