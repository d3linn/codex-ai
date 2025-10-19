from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, cast

import bcrypt
from jose import JWTError, jwt
from pydantic import ValidationError

from app.core.config import get_settings
from app.models.schemas import TokenPayload


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check whether a plaintext password matches its hashed counterpart.

    Args:
        plain_password: Password provided by the user.
        hashed_password: Stored bcrypt hash to compare against.

    Returns:
        bool: ``True`` when the password is valid, otherwise ``False``.
    """
    try:
        plain_bytes = plain_password.encode("utf-8")
        hashed_bytes = hashed_password.encode("utf-8")
    except UnicodeError:
        return False
    try:
        return bool(bcrypt.checkpw(plain_bytes, hashed_bytes))
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash for the provided password.

    Args:
        password: Plaintext password to hash.

    Returns:
        str: Secure bcrypt hash suitable for storage.
    """
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def create_token(subject: str, expires_delta: timedelta, *, token_type: str) -> str:
    """Create a signed JWT for a given subject.

    Args:
        subject: Identifier to embed in the token ``sub`` claim.
        expires_delta: Relative expiry window for the token.

    Returns:
        str: Encoded JWT string.
    """
    settings = get_settings()
    expire = datetime.now(timezone.utc) + expires_delta
    payload: dict[str, Any] = {"sub": subject, "exp": expire, "token_type": token_type}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_token(token: str, *, expected_type: str | None = None) -> TokenPayload:
    """Decode a JWT and return its payload data.

    Args:
        token: Encoded JWT string to validate.
        expected_type: Optional token type that must match the decoded payload.

    Returns:
        TokenPayload: Validated payload data extracted from the token.

    Raises:
        ValueError: If the token is invalid, malformed, or the token type mismatches.
    """
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:  # pragma: no cover - raised for invalid tokens
        raise ValueError("Invalid token") from exc
    try:
        token_payload = cast(TokenPayload, TokenPayload.model_validate(payload))
    except ValidationError as exc:  # pragma: no cover - schema validation failure
        raise ValueError("Invalid token payload") from exc
    if expected_type is not None and token_payload.token_type != expected_type:
        raise ValueError("Invalid token type")
    return token_payload
