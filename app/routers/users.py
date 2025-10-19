from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.models.database import get_session
from app.models.schemas import UserCreate, UserRead, UserUpdate
from app.models.user import User
from app.services.users import create_user, delete_user, get_user, list_users, update_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserRead])
async def read_users(
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> list[UserRead]:
    """List all users in the system.

    Args:
        session: Database session dependency.
        _: Authenticated user dependency (unused).

    Returns:
        list[UserRead]: Collection of persisted users.
    """
    return await list_users(session)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> UserRead:
    """Create a new user record.

    Args:
        user_in: Payload describing the new user.
        session: Database session dependency.
        _: Authenticated user dependency (unused).

    Returns:
        UserRead: The created user data.

    Raises:
        HTTPException: Raised when the email already exists.
    """
    try:
        return await create_user(session, user_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> UserRead:
    """Retrieve a single user by identifier.

    Args:
        user_id: Identifier of the user to retrieve.
        session: Database session dependency.
        _: Authenticated user dependency (unused).

    Returns:
        UserRead: The requested user data.

    Raises:
        HTTPException: Raised when the user does not exist.
    """
    user = await get_user(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return cast(UserRead, UserRead.model_validate(user))


@router.put("/{user_id}", response_model=UserRead)
async def update_user_endpoint(
    user_id: int,
    user_in: UserUpdate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> UserRead:
    """Update an existing user record.

    Args:
        user_id: Identifier of the user to update.
        user_in: Incoming modifications for the user.
        session: Database session dependency.
        _: Authenticated user dependency (unused).

    Returns:
        UserRead: The updated user data.

    Raises:
        HTTPException: Raised when the user is not found or email conflicts.
    """
    user = await get_user(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    try:
        return await update_user(session, user, user_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete(
    "/{user_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_user_endpoint(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> Response:
    """Remove a user from the database.

    Args:
        user_id: Identifier of the user to delete.
        session: Database session dependency.
        _: Authenticated user dependency (unused).

    Raises:
        HTTPException: Raised when the user does not exist.
    """
    user = await get_user(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await delete_user(session, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

