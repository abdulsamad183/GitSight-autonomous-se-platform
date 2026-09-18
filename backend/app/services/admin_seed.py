import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import hash_password
from app.models.user import User
from app.repositories import user_repository

logger = logging.getLogger(__name__)


async def ensure_single_admin(db: AsyncSession, settings: Settings) -> User:
    """Demote any other admins and ensure the configured admin account exists."""
    await user_repository.demote_all_admins(db)
    hashed = hash_password(settings.admin_password)
    admin = await user_repository.upsert_admin_credentials(
        db,
        username=settings.admin_username,
        email=settings.admin_email,
        hashed_password=hashed,
    )
    logger.info("Ensured single admin user email=%s", settings.admin_email)
    return admin
