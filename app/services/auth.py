from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import create_token, verify_password
from app.models.schemas import TokenPair
from app.models.user import User
from app.services.users import get_user_by_email


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User:
    user = await get_user_by_email(session, email)
    if user is None:
        raise ValueError("Invalid credentials")
    if not verify_password(password, user.hashed_password):
        raise ValueError("Invalid credentials")
    return user


async def create_token_pair(user: User) -> TokenPair:
    settings = get_settings()
    access_token = create_token(
        subject=user.email,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token = create_token(
        subject=user.email,
        expires_delta=timedelta(minutes=settings.refresh_token_expire_minutes),
    )
    return TokenPair(access_token=access_token, refresh_token=refresh_token)
