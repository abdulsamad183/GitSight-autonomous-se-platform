from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession,
    username: str,
    email: str,
    hashed_password: str,
    role: str = "user",
) -> User:
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def list_admins(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).where(User.role == "admin"))
    return list(result.scalars().all())


async def demote_all_admins(db: AsyncSession) -> None:
    result = await db.execute(select(User).where(User.role == "admin"))
    for user in result.scalars().all():
        user.role = "user"
    await db.flush()


async def upsert_admin_credentials(
    db: AsyncSession,
    *,
    username: str,
    email: str,
    hashed_password: str,
) -> User:
    """Ensure exactly one admin exists for the given email (caller demotes others first)."""
    user = await get_by_email(db, email)
    if user is None:
        name_owner = await get_by_username(db, username)
        final_username = username if name_owner is None else f"{username}_{email.split('@')[0]}"
        user = User(
            username=final_username,
            email=email,
            hashed_password=hashed_password,
            role="admin",
        )
        db.add(user)
    else:
        if user.username != username:
            name_owner = await get_by_username(db, username)
            if name_owner is None or name_owner.id == user.id:
                user.username = username
        user.hashed_password = hashed_password
        user.role = "admin"
    await db.commit()
    await db.refresh(user)
    return user
