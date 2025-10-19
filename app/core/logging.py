from __future__ import annotations

import contextvars
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

try:  # pragma: no cover - executed only when structlog is available at runtime
    import structlog as _structlog
except ModuleNotFoundError:  # pragma: no cover - fallback when structlog is absent
    _structlog = None

structlog: Any | None = _structlog

_REQUEST_CONTEXT: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar(
    "request_context", default={}
)


@dataclass
class _FallbackLogger:
    """Provide a structlog-like interface backed by ``logging.Logger``."""

    name: str | None
    _context: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._logger = logging.getLogger(self.name)

    def bind(self, **kwargs: Any) -> "_FallbackLogger":
        """Attach contextual data to subsequent log entries."""

        self._context.update(kwargs)
        return self

    def new(self, **kwargs: Any) -> "_FallbackLogger":
        """Return a new logger inheriting existing context."""

        combined = {**self._context, **kwargs}
        return _FallbackLogger(self.name, combined)

    def _log(self, level: int, event: str, **kwargs: Any) -> None:
        contextual_data = dict(_REQUEST_CONTEXT.get())
        contextual_data.update(self._context)
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "logger": self.name or "app",
            "level": logging.getLevelName(level).lower(),
            "event": event,
            **contextual_data,
            **kwargs,
        }
        message = json.dumps(payload, default=str)
        self._logger.log(level, message)

    def info(self, event: str, **kwargs: Any) -> None:
        """Log an informational event."""

        self._log(logging.INFO, event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        """Log a warning event."""

        self._log(logging.WARNING, event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        """Log an error event."""

        self._log(logging.ERROR, event, **kwargs)

    def debug(self, event: str, **kwargs: Any) -> None:
        """Log a debug event."""

        self._log(logging.DEBUG, event, **kwargs)


def configure_logging() -> None:
    """Configure structured logging using structlog when available."""

    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout, force=True)
    if structlog is None:
        return
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            timestamper,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.EventRenamer(to="message"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> Any:
    """Return a structlog logger or a JSON-emitting fallback."""

    if structlog is None:
        return _FallbackLogger(name)
    if name is None:
        return structlog.get_logger()
    return structlog.get_logger(name)


def bind_contextvars(**kwargs: Any) -> None:
    """Attach contextual values to the current logging scope.

    Args:
        **kwargs: Key-value pairs to bind for subsequent log entries.
    """

    if structlog is not None:
        structlog.contextvars.bind_contextvars(**kwargs)
        return
    current = dict(_REQUEST_CONTEXT.get())
    current.update(kwargs)
    _REQUEST_CONTEXT.set(current)


def clear_contextvars() -> None:
    """Clear any contextual values bound to the logging scope."""

    if structlog is not None:
        structlog.contextvars.clear_contextvars()
        return
    _REQUEST_CONTEXT.set({})
