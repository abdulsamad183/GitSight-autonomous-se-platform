"""Multi-branch analysis: unique snapshot per branch, repository branch metadata."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "repositories",
        sa.Column("branches_analyzed_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "repositories",
        sa.Column("branches_truncated", sa.Boolean(), nullable=False, server_default="false"),
    )

    # Remove duplicate (repository_id, branch) rows keeping the newest analyzed_at
    op.execute(
        """
        DELETE FROM repository_snapshots rs
        USING repository_snapshots rs2
        WHERE rs.repository_id = rs2.repository_id
          AND rs.branch = rs2.branch
          AND rs.analyzed_at < rs2.analyzed_at
        """
    )

    op.create_unique_constraint(
        "uq_repository_snapshots_repo_branch",
        "repository_snapshots",
        ["repository_id", "branch"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_repository_snapshots_repo_branch",
        "repository_snapshots",
        type_="unique",
    )
    op.drop_column("repositories", "branches_truncated")
    op.drop_column("repositories", "branches_analyzed_count")
