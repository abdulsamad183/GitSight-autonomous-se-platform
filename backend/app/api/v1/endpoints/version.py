from fastapi import APIRouter, Depends

from app.core.config import Settings, get_settings

router = APIRouter()


@router.get("/version")
async def get_version(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {
        "service": settings.service_name,
        "version": settings.version,
    }
