from __future__ import annotations

from typing import cast

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.schemas import UserCreate, UserRead, UserUpdate
from app.models.user import User


async def list_users(session: AsyncSession) -> list[UserRead]:
    result = await session.scalars(select(User))
    users = result.all()
    return [cast(UserRead, UserRead.model_validate(user)) for user in users]


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    user = await session.get(User, user_id)
    return cast(User | None, user)


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    return cast(User | None, user)


async def create_user(session: AsyncSession, user_in: UserCreate) -> UserRead:
    hashed_password = get_password_hash(user_in.password)
    user = User(name=user_in.name, email=user_in.email, hashed_password=hashed_password)
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ValueError("Email already registered") from exc
    await session.refresh(user)
    return cast(UserRead, UserRead.model_validate(user))


async def update_user(session: AsyncSession, user: User, user_in: UserUpdate) -> UserRead:
    if user_in.name is not None:
        user.name = user_in.name
    if user_in.email is not None:
        user.email = user_in.email
    if user_in.password is not None:
        user.hashed_password = get_password_hash(user_in.password)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ValueError("Email already registered") from exc
    await session.refresh(user)
    return cast(UserRead, UserRead.model_validate(user))


async def delete_user(session: AsyncSession, user: User) -> None:
    await session.delete(user)
    await session.commit()

