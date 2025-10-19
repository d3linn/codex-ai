from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app import main as main_module
from app.main import app
from app.models.database import Base, get_session


class SimpleResponse:
    def __init__(self, status_code: int, headers: dict[str, str], body: bytes) -> None:
        self.status_code = status_code
        self.headers = headers
        self._body = body

    def json(self) -> Any:
        if not self._body:
            return None
        return json.loads(self._body.decode())

    def text(self) -> str:
        return self._body.decode()


class SimpleAsyncClient:
    def __init__(self, app_callable: Any) -> None:
        self._app = app_callable

    async def _request(
        self,
        method: str,
        url: str,
        *,
        json_body: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> SimpleResponse:
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
            return await receive_queue.get()

        response_start: dict[str, Any] | None = None
        body_parts: list[bytes] = []

        async def send(message: dict[str, Any]) -> None:
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
        return await self._request("GET", url, headers=headers)

    async def post(
        self,
        url: str,
        *,
        json: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> SimpleResponse:
        return await self._request("POST", url, json_body=json, headers=headers)

    async def put(
        self,
        url: str,
        *,
        json: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> SimpleResponse:
        return await self._request("PUT", url, json_body=json, headers=headers)

    async def delete(self, url: str, *, headers: dict[str, str] | None = None) -> SimpleResponse:
        return await self._request("DELETE", url, headers=headers)


@pytest.fixture
async def client(tmp_path: Path) -> AsyncGenerator[SimpleAsyncClient, None]:
    database_path = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    original_engine = main_module.engine
    main_module.engine = engine

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

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
