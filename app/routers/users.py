from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
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
    return await list_users(session)


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    user_in: UserCreate,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> UserRead:
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
    user = await get_user(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    try:
        return await update_user(session, user, user_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: int,
    session: AsyncSession = Depends(get_session),
    _: User = Depends(get_current_user),
) -> None:
    user = await get_user(session, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    await delete_user(session, user)

