from __future__ import annotations

import time
from typing import Awaitable, Callable
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import bind_contextvars, clear_contextvars, get_logger


logger = get_logger(name=__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach observability context and request identifiers to responses."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Bind a unique request ID and log request lifecycle events.

        Args:
            request: Incoming HTTP request object.
            call_next: Callable that executes the remaining ASGI stack.

        Returns:
            Response: Response returned by the downstream application.

        Raises:
            Exception: Propagates any exception raised by the downstream stack.
        """

        request_id = str(uuid4())
        clear_contextvars()
        bind_contextvars(request_id=request_id, http_method=request.method, http_path=request.url.path)
        start_time = time.perf_counter()
        logger.info("request_started", request_id=request_id, method=request.method, path=request.url.path)
        try:
            response = await call_next(request)
        except Exception:
            duration = time.perf_counter() - start_time
            logger.error(
                "request_failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration=duration,
            )
            clear_contextvars()
            raise
        duration = time.perf_counter() - start_time
        response.headers["x-request-id"] = request_id
        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration=duration,
        )
        clear_contextvars()
        return response
