from __future__ import annotations

from fastapi import APIRouter
from starlette.responses import Response

from app.core.metrics import render_metrics


router = APIRouter()


@router.get("/metrics", include_in_schema=False)
def get_metrics() -> Response:
    """Expose Prometheus-formatted metrics for scraping."""

    return render_metrics()
