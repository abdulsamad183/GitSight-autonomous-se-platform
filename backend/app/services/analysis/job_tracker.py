from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job, JobStatus
from app.repositories import job_event_repository, job_repository

STAGE_CLONING = ("Cloning Repository", 5)
STAGE_DISCOVERING = ("Discovering Branches", 12)
STAGE_CLEANING = ("Cleaning Temporary Files", 95)
STAGE_COMPLETED = ("Completed", 100)


class JobTracker:
    def __init__(self, db: AsyncSession, job: Job) -> None:
        self.db = db
        self.job = job

    async def set_stage(self, stage: tuple[str, float]) -> None:
        name, progress = stage
        await job_repository.update_progress(
            self.db,
            self.job,
            status=JobStatus.RUNNING,
            progress=progress,
            current_stage=name,
        )
        await job_event_repository.append(self.db, job_id=self.job.id, message=name)
        await self.db.commit()

    async def set_message(self, message: str, progress: float | None = None) -> None:
        kwargs: dict = {"status": JobStatus.RUNNING, "current_stage": message}
        if progress is not None:
            kwargs["progress"] = progress
        await job_repository.update_progress(self.db, self.job, **kwargs)
        await job_event_repository.append(self.db, job_id=self.job.id, message=message)
        await self.db.commit()

    async def set_branch_stage(
        self,
        *,
        branch: str,
        branch_index: int,
        total_branches: int,
        sub_stage: str,
        sub_progress: float,
    ) -> None:
        branch_base = 15.0
        branch_span = 75.0
        branch_offset = branch_span * (branch_index / total_branches)
        branch_inner = (branch_span / total_branches) * (sub_progress / 100.0)
        progress = min(90.0, branch_base + branch_offset + branch_inner)
        message = f"Analyzing branch {branch} ({branch_index + 1}/{total_branches}): {sub_stage}"
        await self.set_message(message, progress=progress)

    async def mark_running(self) -> None:
        await job_repository.update_progress(
            self.db,
            self.job,
            status=JobStatus.RUNNING,
            progress=0.0,
            current_stage="Starting analysis",
        )
        await self.db.commit()

    async def mark_completed(self) -> None:
        await job_repository.update_progress(
            self.db,
            self.job,
            status=JobStatus.COMPLETED,
            progress=100.0,
            current_stage=STAGE_COMPLETED[0],
        )
        await job_event_repository.append(
            self.db, job_id=self.job.id, message=STAGE_COMPLETED[0]
        )
        await self.db.commit()

    async def mark_completed_with_stage(self, stage: str) -> None:
        await job_repository.update_progress(
            self.db,
            self.job,
            status=JobStatus.COMPLETED,
            progress=100.0,
            current_stage=stage,
        )
        await job_event_repository.append(self.db, job_id=self.job.id, message=stage)
        await self.db.commit()

    async def mark_failed(self, error: str) -> None:
        await job_repository.update_progress(
            self.db,
            self.job,
            status=JobStatus.FAILED,
            current_stage="Failed",
            error_message=error,
        )
        await job_event_repository.append(self.db, job_id=self.job.id, message=f"Failed: {error}")
        await self.db.commit()
