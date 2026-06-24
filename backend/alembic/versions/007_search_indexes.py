"""Add FTS search_vector on code_chunks and HNSW index on chunk_embeddings."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE code_chunks
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            setweight(to_tsvector('simple', coalesce(symbol_name, '')), 'A') ||
            setweight(to_tsvector('simple', coalesce(file_path, '')), 'B') ||
            setweight(to_tsvector('simple', coalesce(content, '')), 'C')
        ) STORED
        """
    )
    op.create_index(
        "ix_code_chunks_search_vector",
        "code_chunks",
        ["search_vector"],
        unique=False,
        postgresql_using="gin",
    )
    op.execute(
        """
        CREATE INDEX ix_chunk_embeddings_hnsw
        ON chunk_embeddings
        USING hnsw (embedding vector_cosine_ops)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_chunk_embeddings_hnsw")
    op.drop_index("ix_code_chunks_search_vector", table_name="code_chunks")
    op.drop_column("code_chunks", "search_vector")
