from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.models.database import get_session
from app.models.schemas import RefreshRequest, TokenPair, UserCreate, UserLogin, UserRead
from app.services.auth import authenticate_user, create_token_pair
from app.services.users import create_user, get_user_by_email

router = APIRouter()


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def signup(user_in: UserCreate, session: AsyncSession = Depends(get_session)) -> UserRead:
    """Register a new user account.

    Args:
        user_in: Incoming payload with the user details.
        session: Database session dependency.

    Returns:
        UserRead: The persisted user information.

    Raises:
        HTTPException: Raised when the email is already registered.
    """
    try:
        return await create_user(session, user_in)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/login", response_model=TokenPair)
async def login(credentials: UserLogin, session: AsyncSession = Depends(get_session)) -> TokenPair:
    """Authenticate a user and issue an access and refresh token pair.

    Args:
        credentials: Login credentials submitted by the user.
        session: Database session dependency.

    Returns:
        TokenPair: Newly generated access and refresh tokens.

    Raises:
        HTTPException: Raised when credentials are invalid.
    """
    try:
        user = await authenticate_user(session, credentials.email, credentials.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    return await create_token_pair(user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(request: RefreshRequest, session: AsyncSession = Depends(get_session)) -> TokenPair:
    """Refresh authentication tokens using a valid refresh token.

    Args:
        request: Payload containing the refresh token.
        session: Database session dependency.

    Returns:
        TokenPair: Refreshed access and refresh tokens.

    Raises:
        HTTPException: Raised when the token is invalid or the user no longer exists.
    """
    try:
        payload = decode_token(request.refresh_token, expected_type="refresh")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    user = await get_user_by_email(session, payload.sub)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return await create_token_pair(user)
