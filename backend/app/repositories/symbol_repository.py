from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.symbol import Symbol, SymbolType
from app.schemas.analysis import SymbolCreate


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
    return records
