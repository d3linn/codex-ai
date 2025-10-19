from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import main as main_module
from app.core.deps import get_summarization_service
from app.main import app
from app.models.database import Base, get_session


class SimpleResponse:
    """Minimal response wrapper for interacting with ASGI apps in tests."""

    def __init__(self, status_code: int, headers: dict[str, str], body: bytes) -> None:
        """Initialize the response wrapper.

        Args:
            status_code: HTTP status code from the ASGI response.
            headers: Response headers keyed by lowercase names.
            body: Raw response body bytes.
        """
        self.status_code = status_code
        self.headers = headers
        self._body = body

    def json(self) -> Any:
        """Return the response payload parsed as JSON.

        Returns:
            Any: Parsed JSON content or ``None`` if the body is empty.
        """
        if not self._body:
            return None
        return json.loads(self._body.decode())

    def text(self) -> str:
        """Return the response body decoded as UTF-8 text.

        Returns:
            str: Decoded response body.
        """
        return self._body.decode()


class SimpleAsyncClient:
    """Lightweight async HTTP client tailored for FastAPI integration tests."""

    def __init__(self, app_callable: Any) -> None:
        """Create an async client for invoking an ASGI callable.

        Args:
            app_callable: ASGI application to exercise.
        """
        self._app = app_callable

    async def _request(
        self,
        method: str,
        url: str,
        *,
        json_body: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> SimpleResponse:
        """Perform an HTTP request against the ASGI application.

        Args:
            method: HTTP method name.
            url: Target URL path or absolute URL.
            json_body: Optional JSON serializable payload.
            headers: Optional headers to include in the request.

        Returns:
            SimpleResponse: Wrapped ASGI response.
        """
        parsed = urlsplit(url)
        path = parsed.path or url
        query_string = parsed.query.encode()

        header_items: list[tuple[bytes, bytes]] = []
        if headers is not None:
            header_items.extend((key.lower().encode(), value.encode()) for key, value in headers.items())

        body = b""
        if json_body is not None:
            body = json.dumps(json_body).encode()
            header_items.append((b"content-type", b"application/json"))
            header_items.append((b"content-length", str(len(body)).encode()))

        scope = {
            "type": "http",
            "http_version": "1.1",
            "asgi": {"version": "3.0"},
            "method": method.upper(),
            "scheme": "http",
            "path": path,
            "raw_path": path.encode(),
            "query_string": query_string,
            "headers": header_items,
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
        }

        receive_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        await receive_queue.put({"type": "http.request", "body": body, "more_body": False})

        async def receive() -> dict[str, Any]:
            """Return the next ASGI receive message from the queue.

            Returns:
                dict[str, Any]: Message consumed from the queue.
            """
            return await receive_queue.get()

        response_start: dict[str, Any] | None = None
        body_parts: list[bytes] = []

        async def send(message: dict[str, Any]) -> None:
            """Collect ASGI send events produced by the application.

            Args:
                message: ASGI protocol message emitted by the app.
            """
            nonlocal response_start
            if message["type"] == "http.response.start":
                response_start = message
            elif message["type"] == "http.response.body":
                body_parts.append(message.get("body", b""))

        await self._app(scope, receive, send)
        assert response_start is not None
        status_code = int(response_start["status"])
        raw_headers = response_start.get("headers", [])
        response_headers = {key.decode(): value.decode() for key, value in raw_headers}
        return SimpleResponse(status_code, response_headers, b"".join(body_parts))

    async def get(self, url: str, *, headers: dict[str, str] | None = None) -> SimpleResponse:
        """Send a GET request.

        Args:
            url: Target URL path or absolute URL.
            headers: Optional request headers.

        Returns:
            SimpleResponse: Wrapped ASGI response.
        """
        return await self._request("GET", url, headers=headers)

    async def post(
        self,
        url: str,
        *,
        json: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> SimpleResponse:
        """Send a POST request with an optional JSON body.

        Args:
            url: Target URL path or absolute URL.
            json: JSON payload to include in the request body.
            headers: Optional request headers.

        Returns:
            SimpleResponse: Wrapped ASGI response.
        """
        return await self._request("POST", url, json_body=json, headers=headers)

    async def put(
        self,
        url: str,
        *,
        json: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> SimpleResponse:
        """Send a PUT request with an optional JSON body.

        Args:
            url: Target URL path or absolute URL.
            json: JSON payload to include in the request body.
            headers: Optional request headers.

        Returns:
            SimpleResponse: Wrapped ASGI response.
        """
        return await self._request("PUT", url, json_body=json, headers=headers)

    async def delete(self, url: str, *, headers: dict[str, str] | None = None) -> SimpleResponse:
        """Send a DELETE request.

        Args:
            url: Target URL path or absolute URL.
            headers: Optional request headers.

        Returns:
            SimpleResponse: Wrapped ASGI response.
        """
        return await self._request("DELETE", url, headers=headers)


@pytest_asyncio.fixture
async def client(tmp_path: Path) -> AsyncGenerator[SimpleAsyncClient, None]:
    """Provide a test client backed by an isolated SQLite database.

    Yields:
        SimpleAsyncClient: Client bound to the temporary application setup.
    """
    database_path = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    original_engine = main_module.engine
    main_module.engine = engine

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        """Yield sessions bound to the temporary test database.

        Yields:
            AsyncSession: Session connected to the isolated database.
        """
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    class _FakeSummarizationService:
        """Deterministic summarization stub for tests."""

        async def summarize(self, text: str) -> str:
            """Return a reproducible summary for the provided text."""

            stripped = text.strip()
            if not stripped:
                raise ValueError("Text must not be empty")
            return f"summary:{len(stripped)}"

    app.dependency_overrides[get_summarization_service] = lambda: _FakeSummarizationService()

    await app.router.startup()
    simple_client = SimpleAsyncClient(app)
    try:
        yield simple_client
    finally:
        await app.router.shutdown()
        app.dependency_overrides.clear()
        main_module.engine = original_engine
        await engine.dispose()
        if database_path.exists():
            database_path.unlink()
