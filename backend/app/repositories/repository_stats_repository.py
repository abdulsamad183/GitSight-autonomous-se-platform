from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.dependency_edge import DependencyEdge
from app.models.file import File
from app.models.job import Job, JobStatus
from app.models.symbol import Symbol, SymbolType


@dataclass
class RepositoryStats:
    files_count: int
    classes_count: int
    functions_count: int
    methods_count: int
    dependencies_count: int
    analysis_status: str
    language_breakdown: dict[str, int]


async def get_latest_job_status(db: AsyncSession, repository_id: UUID) -> str:
    result = await db.execute(
        select(Job.status)
        .where(Job.repository_id == repository_id)
        .order_by(Job.created_at.desc())
        .limit(1)
    )
    status = result.scalar_one_or_none()
    if status is None:
        return "UNKNOWN"
    if status == JobStatus.QUEUED:
        return "PENDING"
    return status.value.upper()


async def get_language_breakdown_for_snapshot(
    db: AsyncSession, snapshot_id: UUID
) -> dict[str, int]:
    result = await db.execute(
        select(File.language, func.count())
        .where(File.snapshot_id == snapshot_id)
        .group_by(File.language)
    )
    breakdown: dict[str, int] = {}
    for language, count in result.all():
        key = language or "unknown"
        breakdown[key] = int(count)
    return dict(sorted(breakdown.items(), key=lambda item: (-item[1], item[0])))


async def get_stats_for_snapshot(db: AsyncSession, snapshot_id: UUID) -> RepositoryStats:
    files_count = await db.scalar(
        select(func.count()).select_from(File).where(File.snapshot_id == snapshot_id)
    )
    classes_count = await db.scalar(
        select(func.count())
        .select_from(Symbol)
        .where(Symbol.snapshot_id == snapshot_id, Symbol.symbol_type == SymbolType.CLASS)
    )
    functions_count = await db.scalar(
        select(func.count())
        .select_from(Symbol)
        .where(Symbol.snapshot_id == snapshot_id, Symbol.symbol_type == SymbolType.FUNCTION)
    )
    methods_count = await db.scalar(
        select(func.count())
        .select_from(Symbol)
        .where(Symbol.snapshot_id == snapshot_id, Symbol.symbol_type == SymbolType.METHOD)
    )
    dependencies_count = await db.scalar(
        select(func.count())
        .select_from(DependencyEdge)
        .where(DependencyEdge.snapshot_id == snapshot_id)
    )
    language_breakdown = await get_language_breakdown_for_snapshot(db, snapshot_id)

    return RepositoryStats(
        files_count=files_count or 0,
        classes_count=classes_count or 0,
        functions_count=functions_count or 0,
        methods_count=methods_count or 0,
        dependencies_count=dependencies_count or 0,
        analysis_status="",
        language_breakdown=language_breakdown,
    )
