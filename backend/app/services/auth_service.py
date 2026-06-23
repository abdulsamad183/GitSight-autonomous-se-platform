from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories import user_repository
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.exceptions import AuthenticationError, ConflictError


async def register(db: AsyncSession, data: RegisterRequest) -> User:
    if await user_repository.get_by_email(db, data.email):
        raise ConflictError("Email already registered")
    if await user_repository.get_by_username(db, data.username):
        raise ConflictError("Username already taken")

    hashed = hash_password(data.password)
    return await user_repository.create(db, data.username, data.email, hashed)


async def authenticate(db: AsyncSession, data: LoginRequest) -> User:
    user = await user_repository.get_by_email(db, data.email)
    if not user or not verify_password(data.password, user.hashed_password):
        raise AuthenticationError("Invalid email or password")
    return user


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User:
    user = await user_repository.get_by_id(db, user_id)
    if not user:
        raise AuthenticationError("Invalid or expired token")
    return user
