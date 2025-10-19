from __future__ import annotations

from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.privacy import hash_identifier
from app.core.security import create_token, verify_password
from app.models.schemas import TokenPair
from app.models.user import User
from app.services.users import get_user_by_email


logger = get_logger(name=__name__)


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User:
    """Validate user credentials and return the matching user.

    Args:
        session: Database session used for lookups.
        email: Email address provided by the user.
        password: Plaintext password to verify.

    Returns:
        User: The authenticated user entity.

    Raises:
        ValueError: If the credentials are invalid.
    """
    user = await get_user_by_email(session, email)
    if user is None:
        logger.warning("authenticate_user_missing", email_hash=hash_identifier(email))
        raise ValueError("Invalid credentials")
    if not verify_password(password, user.hashed_password):
        logger.warning(
            "authenticate_user_invalid_password", email_hash=hash_identifier(email)
        )
        raise ValueError("Invalid credentials")
    logger.info(
        "authenticate_user_success", user_id=user.id, email_hash=hash_identifier(email)
    )
    return user


async def create_token_pair(user: User) -> TokenPair:
    """Create an access and refresh token pair for a user.

    Args:
        user: Authenticated user for whom tokens are generated.

    Returns:
        TokenPair: Newly generated access and refresh tokens.
    """
    settings = get_settings()
    access_token = create_token(
        subject=user.email,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        token_type="access",
    )
    refresh_token = create_token(
        subject=user.email,
        expires_delta=timedelta(minutes=settings.refresh_token_expire_minutes),
        token_type="refresh",
    )
    logger.info("create_token_pair", user_id=user.id, email_hash=hash_identifier(user.email))
    return TokenPair(access_token=access_token, refresh_token=refresh_token)
