"""Repository understanding: snapshots, files, symbols, dependency_edges, job_events."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

symbol_type = postgresql.ENUM("class", "function", "method", name="symbol_type", create_type=False)
dependency_type = postgresql.ENUM(
    "IMPORT", "FROM_IMPORT", "REQUIRE", "INCLUDE", name="dependency_type", create_type=False
)


def upgrade() -> None:
    symbol_type.create(op.get_bind(), checkfirst=True)
    dependency_type.create(op.get_bind(), checkfirst=True)

    op.add_column("repositories", sa.Column("owner", sa.String(length=255), nullable=True))
    op.add_column(
        "repositories", sa.Column("repository_name", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "repositories", sa.Column("default_branch", sa.String(length=255), nullable=True)
    )
    op.add_column(
        "repositories", sa.Column("latest_commit_hash", sa.String(length=40), nullable=True)
    )
    op.create_index(
        op.f("ix_repositories_latest_commit_hash"),
        "repositories",
        ["latest_commit_hash"],
        unique=False,
    )

    op.execute(
        """
        UPDATE repositories
        SET owner = 'unknown',
            repository_name = name
        WHERE owner IS NULL
        """
    )
    op.alter_column("repositories", "owner", nullable=False)
    op.alter_column("repositories", "repository_name", nullable=False)

    op.add_column("jobs", sa.Column("current_stage", sa.String(length=128), nullable=True))
    op.add_column("jobs", sa.Column("error_message", sa.Text(), nullable=True))

    op.create_table(
        "repository_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("commit_hash", sa.String(length=40), nullable=False),
        sa.Column("branch", sa.String(length=255), nullable=False),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
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
        op.f("ix_repository_snapshots_repository_id"),
        "repository_snapshots",
        ["repository_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_repository_snapshots_commit_hash"),
        "repository_snapshots",
        ["commit_hash"],
        unique=False,
    )

    op.create_table(
        "files",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relative_path", sa.String(length=1024), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("extension", sa.String(length=32), nullable=True),
        sa.Column("language", sa.String(length=32), nullable=True),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("is_binary", sa.Boolean(), nullable=False, server_default="false"),
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
        sa.ForeignKeyConstraint(["snapshot_id"], ["repository_snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_files_repository_id"), "files", ["repository_id"], unique=False)
    op.create_index(op.f("ix_files_snapshot_id"), "files", ["snapshot_id"], unique=False)
    op.create_index(
        "ix_files_snapshot_relative_path", "files", ["snapshot_id", "relative_path"], unique=False
    )

    op.create_table(
        "symbols",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("symbol_name", sa.String(length=512), nullable=False),
        sa.Column("symbol_type", symbol_type, nullable=False),
        sa.Column("start_line", sa.Integer(), nullable=False),
        sa.Column("end_line", sa.Integer(), nullable=False),
        sa.Column("signature", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["snapshot_id"], ["repository_snapshots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_symbols_repository_id"), "symbols", ["repository_id"], unique=False)
    op.create_index(op.f("ix_symbols_snapshot_id"), "symbols", ["snapshot_id"], unique=False)
    op.create_index(op.f("ix_symbols_file_id"), "symbols", ["file_id"], unique=False)

    op.create_table(
        "dependency_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("repository_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("snapshot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_file_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dependency_type", dependency_type, nullable=False),
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
        sa.ForeignKeyConstraint(["snapshot_id"], ["repository_snapshots.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["source_file_id"], ["files.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_file_id"], ["files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_dependency_edges_repository_id"),
        "dependency_edges",
        ["repository_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dependency_edges_snapshot_id"),
        "dependency_edges",
        ["snapshot_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dependency_edges_source_file_id"),
        "dependency_edges",
        ["source_file_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_dependency_edges_target_file_id"),
        "dependency_edges",
        ["target_file_id"],
        unique=False,
    )

    op.create_table(
        "job_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
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
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_events_job_id"), "job_events", ["job_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_job_events_job_id"), table_name="job_events")
    op.drop_table("job_events")
    op.drop_index(op.f("ix_dependency_edges_target_file_id"), table_name="dependency_edges")
    op.drop_index(op.f("ix_dependency_edges_source_file_id"), table_name="dependency_edges")
    op.drop_index(op.f("ix_dependency_edges_snapshot_id"), table_name="dependency_edges")
    op.drop_index(op.f("ix_dependency_edges_repository_id"), table_name="dependency_edges")
    op.drop_table("dependency_edges")
    op.drop_index(op.f("ix_symbols_file_id"), table_name="symbols")
    op.drop_index(op.f("ix_symbols_snapshot_id"), table_name="symbols")
    op.drop_index(op.f("ix_symbols_repository_id"), table_name="symbols")
    op.drop_table("symbols")
    op.drop_index("ix_files_snapshot_relative_path", table_name="files")
    op.drop_index(op.f("ix_files_snapshot_id"), table_name="files")
    op.drop_index(op.f("ix_files_repository_id"), table_name="files")
    op.drop_table("files")
    op.drop_index(op.f("ix_repository_snapshots_commit_hash"), table_name="repository_snapshots")
    op.drop_index(op.f("ix_repository_snapshots_repository_id"), table_name="repository_snapshots")
    op.drop_table("repository_snapshots")
    op.drop_column("jobs", "error_message")
    op.drop_column("jobs", "current_stage")
    op.drop_index(op.f("ix_repositories_latest_commit_hash"), table_name="repositories")
    op.drop_column("repositories", "latest_commit_hash")
    op.drop_column("repositories", "default_branch")
    op.drop_column("repositories", "repository_name")
    op.drop_column("repositories", "owner")
    dependency_type.drop(op.get_bind(), checkfirst=True)
    symbol_type.drop(op.get_bind(), checkfirst=True)
