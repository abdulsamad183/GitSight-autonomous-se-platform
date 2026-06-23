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

    return RepositoryStats(
        files_count=files_count or 0,
        classes_count=classes_count or 0,
        functions_count=functions_count or 0,
        methods_count=methods_count or 0,
        dependencies_count=dependencies_count or 0,
        analysis_status="",
    )
