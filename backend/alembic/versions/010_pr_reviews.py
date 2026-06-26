"""Add pr_reviews table for cached AI pull request reviews."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: Union[str, None] = "009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "pr_reviews",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("repository_id", sa.UUID(), nullable=False),
        sa.Column("pull_request_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(["pull_request_id"], ["pull_requests.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("repository_id", "pull_request_id", name="uq_pr_reviews_repo_pr"),
    )
    op.create_index("ix_pr_reviews_repository_id", "pr_reviews", ["repository_id"], unique=False)
    op.create_index("ix_pr_reviews_pull_request_id", "pr_reviews", ["pull_request_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_pr_reviews_pull_request_id", table_name="pr_reviews")
    op.drop_index("ix_pr_reviews_repository_id", table_name="pr_reviews")
    op.drop_table("pr_reviews")
