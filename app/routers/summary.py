"""API router exposing text summarization capabilities."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE

from app.ai.summary import SummarizationService
from app.core.deps import get_summarization_service
from app.models.schemas import SummarizeRequest, SummarizeResponse

router = APIRouter(prefix="/summarize", tags=["ai"])


@router.post("", response_model=SummarizeResponse)
async def summarize_text(
    payload: SummarizeRequest,
    service: SummarizationService = Depends(get_summarization_service),
) -> SummarizeResponse:
    """Return a concise summary for the submitted text."""
    try:
        summary = await service.summarize(payload.text)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    return SummarizeResponse(summary=summary)
