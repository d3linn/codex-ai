from __future__ import annotations

import hashlib


def hash_identifier(value: str) -> str:
    """Return a deterministic, truncated digest suitable for logging.

    Args:
        value: Raw string containing potentially sensitive information.

    Returns:
        str: Lowercase hexadecimal digest truncated to 12 characters.
    """

    normalized = value.strip().lower().encode("utf-8", errors="ignore")
    digest = hashlib.sha256(normalized).hexdigest()
    return digest[:12]
