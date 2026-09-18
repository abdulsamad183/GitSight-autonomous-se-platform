from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.user import User
from app.schemas.admin import (
    AdminStatsResponse,
    AdminUserDetailResponse,
    AdminUserListResponse,
)
from app.services import admin_service

router = APIRouter()


@router.get("/stats", response_model=AdminStatsResponse)
async def admin_stats(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> AdminStatsResponse:
    return await admin_service.get_stats(db)


@router.get("/users", response_model=AdminUserListResponse)
async def admin_list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> AdminUserListResponse:
    return await admin_service.list_users(db, page=page, limit=limit)


@router.get("/users/{user_id}", response_model=AdminUserDetailResponse)
async def admin_user_detail(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
) -> AdminUserDetailResponse:
    return await admin_service.get_user_detail(db, user_id)
