from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def read_health() -> dict[str, str]:
    """Return a simple status payload for health checks.

    Returns:
        dict[str, str]: Health status response.
    """
    return {"status": "ok"}
