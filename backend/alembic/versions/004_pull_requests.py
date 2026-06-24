"""Pull request inventory."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

pull_request_state = postgresql.ENUM(
    "open",
    "closed",
    "merged",
    name="pull_request_state",
    create_type=False,
)


def upgrade() -> None:
    pull_request_state.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "pull_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("github_pr_id", sa.BigInteger(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("state", pull_request_state, nullable=False),
        sa.Column("author_username", sa.String(length=255), nullable=False),
        sa.Column("source_branch", sa.String(length=255), nullable=True),
        sa.Column("target_branch", sa.String(length=255), nullable=True),
        sa.Column("github_created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("github_updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("github_closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("github_merged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_draft", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_merged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("html_url", sa.String(length=512), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=False),
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
    )
    op.create_index(
        "uq_pull_requests_repo_github_id",
        "pull_requests",
        ["repository_id", "github_pr_id"],
        unique=True,
    )
    op.create_index(
        "ix_pull_requests_repository_state",
        "pull_requests",
        ["repository_id", "state"],
        unique=False,
    )
    op.create_index(
        op.f("ix_pull_requests_repository_id"),
        "pull_requests",
        ["repository_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_pull_requests_repository_id"), table_name="pull_requests")
    op.drop_index("ix_pull_requests_repository_state", table_name="pull_requests")
    op.drop_index("uq_pull_requests_repo_github_id", table_name="pull_requests")
    op.drop_table("pull_requests")
    pull_request_state.drop(op.get_bind(), checkfirst=True)
