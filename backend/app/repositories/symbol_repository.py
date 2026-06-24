from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.file import File
from app.models.symbol import Symbol, SymbolType
from app.schemas.analysis import SymbolCreate


def _resolve_parent_class_id(
    *,
    classes: list[Symbol],
    parent_class_name: str,
    method_start: int,
    method_end: int,
) -> UUID | None:
    candidates = [cls for cls in classes if cls.symbol_name == parent_class_name]
    if not candidates:
        return None
    if len(candidates) == 1:
        return candidates[0].id

    enclosing = [
        cls for cls in candidates if cls.start_line <= method_start and cls.end_line >= method_end
    ]
    if not enclosing:
        return candidates[0].id

    return min(enclosing, key=lambda cls: cls.end_line - cls.start_line).id


async def bulk_create(
    db: AsyncSession,
    *,
    repository_id: UUID,
    snapshot_id: UUID,
    symbols: list[SymbolCreate],
) -> list[Symbol]:
    records = [
        Symbol(
            repository_id=repository_id,
            snapshot_id=snapshot_id,
            file_id=item.file_id,
            symbol_name=item.symbol_name,
            symbol_type=SymbolType(item.symbol_type),
            start_line=item.start_line,
            end_line=item.end_line,
            signature=item.signature,
        )
        for item in symbols
    ]
    db.add_all(records)
    await db.flush()

    classes_by_file: dict[UUID, list[Symbol]] = {}
    for record in records:
        if record.symbol_type == SymbolType.CLASS:
            classes_by_file.setdefault(record.file_id, []).append(record)

    for record, item in zip(records, symbols, strict=True):
        if record.symbol_type != SymbolType.METHOD or not item.parent_class_name:
            continue
        file_classes = classes_by_file.get(record.file_id, [])
        parent_id = _resolve_parent_class_id(
            classes=file_classes,
            parent_class_name=item.parent_class_name,
            method_start=record.start_line,
            method_end=record.end_line,
        )
        if parent_id is not None:
            record.parent_symbol_id = parent_id

    await db.flush()
    return records


async def list_for_snapshot(
    db: AsyncSession,
    *,
    snapshot_id: UUID,
) -> list[Symbol]:
    result = await db.execute(
        select(Symbol)
        .where(Symbol.snapshot_id == snapshot_id)
        .options(selectinload(Symbol.parent))
        .order_by(Symbol.file_id, Symbol.start_line)
    )
    return list(result.scalars().all())


async def list_for_snapshot_with_files(
    db: AsyncSession,
    *,
    snapshot_id: UUID,
) -> list[tuple[Symbol, File]]:
    result = await db.execute(
        select(Symbol, File)
        .join(File, File.id == Symbol.file_id)
        .where(Symbol.snapshot_id == snapshot_id)
        .options(selectinload(Symbol.parent))
        .order_by(File.relative_path, Symbol.start_line)
    )
    return list(result.all())
