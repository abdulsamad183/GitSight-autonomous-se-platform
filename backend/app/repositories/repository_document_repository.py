from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.repository_document import (
    DocumentGeneratedBy,
    DocumentType,
    RepositoryDocument,
)


async def get_by_type(
    db: AsyncSession,
    *,
    repository_id: UUID,
    document_type: DocumentType,
) -> RepositoryDocument | None:
    result = await db.execute(
        select(RepositoryDocument).where(
            RepositoryDocument.repository_id == repository_id,
            RepositoryDocument.document_type == document_type,
        )
    )
    return result.scalar_one_or_none()


async def list_for_repository(
    db: AsyncSession,
    *,
    repository_id: UUID,
) -> list[RepositoryDocument]:
    result = await db.execute(
        select(RepositoryDocument)
        .where(RepositoryDocument.repository_id == repository_id)
        .order_by(RepositoryDocument.document_type)
    )
    return list(result.scalars().all())


async def upsert(
    db: AsyncSession,
    *,
    repository_id: UUID,
    document_type: DocumentType,
    title: str,
    content: str,
    generated_by: DocumentGeneratedBy,
    source_path: str | None = None,
) -> RepositoryDocument:
    now = datetime.now(timezone.utc)
    stmt = (
        insert(RepositoryDocument)
        .values(
            repository_id=repository_id,
            document_type=document_type,
            title=title,
            content=content,
            generated_by=generated_by,
            generated_at=now,
            source_path=source_path,
        )
        .on_conflict_do_update(
            constraint="uq_repository_documents_type",
            set_={
                "title": title,
                "content": content,
                "generated_by": generated_by,
                "generated_at": now,
                "source_path": source_path,
            },
        )
        .returning(RepositoryDocument)
    )
    result = await db.execute(stmt)
    document = result.scalar_one()
    await db.flush()
    return document


async def delete_by_type(
    db: AsyncSession,
    *,
    repository_id: UUID,
    document_type: DocumentType,
) -> None:
    await db.execute(
        delete(RepositoryDocument).where(
            RepositoryDocument.repository_id == repository_id,
            RepositoryDocument.document_type == document_type,
        )
    )
    await db.flush()
