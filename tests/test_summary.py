from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.ai.summary import OpenAISummarizationService, _extract_summary_text

if TYPE_CHECKING:
    from tests.conftest import SimpleAsyncClient


class _StubContent:
    """Simplified representation of response content blocks."""

    def __init__(self, text: str) -> None:
        self.text = text


class _StubBlock:
    """Container for response content items."""

    def __init__(self, text: str) -> None:
        self.content = [_StubContent(text)]


class _StubResponse:
    """OpenAI-like response object used for testing."""

    def __init__(self, text: str) -> None:
        self.output = [_StubBlock(text)]


class _DumpableResponse:
    """Response variant exposing a model_dump method."""

    def __init__(self, *, content: str | None = None) -> None:
        self._content = content

    def model_dump(self) -> dict[str, str | None]:
        """Return a payload similar to Pydantic models."""

        return {"output_text": self._content}


class _StubResponsesClient:
    """Shim implementing the Responses API surface."""

    def __init__(self, *, text: str, fail: bool = False) -> None:
        self._text = text
        self._fail = fail

    def create(self, **_: object) -> _StubResponse:
        if self._fail:
            raise RuntimeError("request failed")
        return _StubResponse(self._text)


class _StubOpenAIClient:
    """Minimal OpenAI client exposing the responses attribute."""

    def __init__(self, *, text: str, fail: bool = False) -> None:
        self.responses = _StubResponsesClient(text=text, fail=fail)


@pytest.mark.asyncio
async def test_summarize_endpoint_returns_summary(client: "SimpleAsyncClient") -> None:
    """Ensure the summarize endpoint returns the stubbed summary."""

    payload = {"text": "This is a long piece of text that needs a summary."}
    response = await client.post("/summarize", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body == {"summary": "summary:50"}


@pytest.mark.asyncio
async def test_summarize_endpoint_rejects_empty_text(client: "SimpleAsyncClient") -> None:
    """Verify validation errors bubble up for empty payloads."""

    response = await client.post("/summarize", json={"text": "   "})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_openai_summarization_service_generates_summary() -> None:
    """Validate that the OpenAI service delegates to the provided client."""

    service = OpenAISummarizationService(api_key="key", client=_StubOpenAIClient(text="Short summary."))
    summary = await service.summarize("content to summarize")
    assert summary == "Short summary."


@pytest.mark.asyncio
async def test_openai_summarization_service_raises_on_client_failure() -> None:
    """Ensure client failures translate into runtime errors."""

    service = OpenAISummarizationService(api_key="key", client=_StubOpenAIClient(text="", fail=True))
    with pytest.raises(RuntimeError):
        await service.summarize("text to summarize")


@pytest.mark.asyncio
async def test_openai_summarization_service_rejects_empty_text() -> None:
    """Confirm validation prevents sending blank requests to OpenAI."""

    service = OpenAISummarizationService(api_key="key", client=_StubOpenAIClient(text="ignored"))
    with pytest.raises(ValueError):
        await service.summarize("  ")


def test_extract_summary_text_from_choices() -> None:
    """Extract text when responses fallback to the choices field."""

    class _Choice:
        def __init__(self, content: str) -> None:
            self.message = {"content": content}

    response = type("ChoicesResponse", (), {"choices": [_Choice("Choice summary.")]})()
    assert _extract_summary_text(response) == "Choice summary."


def test_extract_summary_text_from_model_dump() -> None:
    """Extract text when the response exposes a model_dump method."""

    response = _DumpableResponse(content="Dump summary.")
    assert _extract_summary_text(response) == "Dump summary."


def test_extract_summary_text_handles_missing_content() -> None:
    """Return an empty string when no known fields contain text."""

    response = type("EmptyResponse", (), {})()
    assert _extract_summary_text(response) == ""
