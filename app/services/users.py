from __future__ import annotations

from typing import cast

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.privacy import hash_identifier
from app.core.security import get_password_hash
from app.models.schemas import UserCreate, UserRead, UserUpdate
from app.models.user import User


logger = get_logger(name=__name__)


async def list_users(session: AsyncSession) -> list[UserRead]:
    """Return all users from the database.

    Args:
        session: Database session used for retrieval.

    Returns:
        list[UserRead]: Serialized user models.
    """
    result = await session.scalars(select(User))
    users = result.all()
    serialized = [cast(UserRead, UserRead.model_validate(user)) for user in users]
    logger.info("list_users", user_count=len(serialized))
    return serialized


async def get_user(session: AsyncSession, user_id: int) -> User | None:
    """Fetch a user by identifier.

    Args:
        session: Database session used for retrieval.
        user_id: Primary key of the user.

    Returns:
        User | None: The matching user or ``None`` if absent.
    """
    user = await session.get(User, user_id)
    logger.info("get_user", user_id=user_id, found=user is not None)
    return cast(User | None, user)


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    """Fetch a user by email address.

    Args:
        session: Database session used for retrieval.
        email: Email address to search.

    Returns:
        User | None: The matching user or ``None`` if absent.
    """
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    logger.info(
        "get_user_by_email",
        email_hash=hash_identifier(email),
        found=user is not None,
    )
    return cast(User | None, user)


async def create_user(session: AsyncSession, user_in: UserCreate) -> UserRead:
    """Create and persist a new user.

    Args:
        session: Database session used for persistence.
        user_in: Data required to create the user.

    Returns:
        UserRead: Serialized representation of the new user.

    Raises:
        ValueError: If the email already exists.
    """
    hashed_password = get_password_hash(user_in.password)
    user = User(name=user_in.name, email=user_in.email, hashed_password=hashed_password)
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        logger.warning(
            "create_user_conflict", email_hash=hash_identifier(user_in.email)
        )
        raise ValueError("Email already registered") from exc
    await session.refresh(user)
    logger.info(
        "create_user_success", user_id=user.id, email_hash=hash_identifier(user.email)
    )
    return cast(UserRead, UserRead.model_validate(user))


async def update_user(session: AsyncSession, user: User, user_in: UserUpdate) -> UserRead:
    """Apply updates to an existing user.

    Args:
        session: Database session used for persistence.
        user: Target user instance to modify.
        user_in: Requested updates for the user.

    Returns:
        UserRead: Serialized representation of the updated user.

    Raises:
        ValueError: If the new email conflicts with an existing account.
    """
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
        logger.warning(
            "update_user_conflict",
            user_id=user.id,
            email_hash=hash_identifier(user_in.email or user.email),
        )
        raise ValueError("Email already registered") from exc
    await session.refresh(user)
    logger.info(
        "update_user_success", user_id=user.id, email_hash=hash_identifier(user.email)
    )
    return cast(UserRead, UserRead.model_validate(user))


async def delete_user(session: AsyncSession, user: User) -> None:
    """Delete a user from the database.

    Args:
        session: Database session used for persistence.
        user: User instance to remove.
    """
    await session.delete(user)
    await session.commit()
    logger.info("delete_user_success", user_id=user.id)

