from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from tests.conftest import SimpleAsyncClient


@pytest.mark.asyncio
async def test_metrics_endpoint_records_latency(client: "SimpleAsyncClient") -> None:
    """Ensure the Prometheus metrics endpoint reports latency histograms."""

    health_response = await client.get("/health")
    assert health_response.status_code == 200

    metrics_response = await client.get("/metrics")
    assert metrics_response.status_code == 200
    body = metrics_response.text()
    assert "app_request_latency_seconds_bucket" in body
