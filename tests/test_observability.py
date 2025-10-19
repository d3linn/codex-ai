from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from app.core.privacy import hash_identifier

if TYPE_CHECKING:
    from tests.conftest import SimpleAsyncClient


def test_hash_identifier_is_deterministic() -> None:
    """Ensure hashing removes PII while remaining deterministic."""

    digest_one = hash_identifier("User@example.com")
    digest_two = hash_identifier("user@example.com")
    assert digest_one == digest_two
    assert len(digest_one) == 12
    assert digest_one.islower()


@pytest.mark.asyncio
async def test_request_context_adds_request_id(client: "SimpleAsyncClient") -> None:
    """Verify that each response includes an ``X-Request-ID`` header.

    Args:
        client: Async client fixture used to call the API.
    """

    first_response = await client.get("/health")
    second_response = await client.get("/health")
    first_request_id = first_response.headers.get("x-request-id")
    second_request_id = second_response.headers.get("x-request-id")
    assert first_request_id
    assert second_request_id
    assert first_request_id != second_request_id
