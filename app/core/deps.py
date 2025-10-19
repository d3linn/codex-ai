from __future__ import annotations

from functools import lru_cache

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.summary import OpenAISummarizationService, SummarizationService
from app.core.config import get_settings
from app.core.security import decode_token
from app.models.database import get_session
from app.models.user import User
from app.services.users import get_user_by_email


http_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(http_bearer),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Resolve the authenticated user from a bearer token.

    Args:
        credentials: Bearer token credentials extracted from the request. If
            ``None``, an authentication error is raised.
        session: Database session used to load the user.

    Returns:
        User: The authenticated user associated with the provided token.

    Raises:
        HTTPException: Raised when the credentials are missing, invalid, or the
            user cannot be found.
    """
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token = credentials.credentials
    try:
        payload = decode_token(token, expected_type="access")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
    user = await get_user_by_email(session, payload.sub)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
        )
    return user


@lru_cache
def _build_summarization_service() -> SummarizationService:
    """Instantiate the OpenAI-backed summarization service.

    Returns:
        SummarizationService: Service implementation backed by OpenAI.

    Raises:
        RuntimeError: If the OpenAI API key has not been configured.
    """

    settings = get_settings()
    if settings.openai_api_key is None or not settings.openai_api_key.strip():
        raise RuntimeError("OPENAI_API_KEY is not configured")
    return OpenAISummarizationService(api_key=settings.openai_api_key)


def get_summarization_service() -> SummarizationService:
    """Provide a cached summarization service instance for dependency injection.

    Returns:
        SummarizationService: Cached summarization service instance.
    """

    return _build_summarization_service()

