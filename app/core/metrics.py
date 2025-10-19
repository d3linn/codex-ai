from __future__ import annotations

import time
from collections import defaultdict
from typing import Any, Awaitable, Callable, Iterable

try:  # pragma: no cover - executed when prometheus_client is installed
    from prometheus_client import CONTENT_TYPE_LATEST, Histogram, generate_latest
except ModuleNotFoundError:  # pragma: no cover - fallback when dependency is absent
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

    _FALLBACK_REGISTRY: list["_Histogram"] = []

    class _HistogramChild:
        """Store observations for a specific label set."""

        def __init__(self, histogram: "_Histogram", labels: tuple[str, ...]) -> None:
            self._histogram = histogram
            self._labels = labels

        def observe(self, value: float) -> None:
            """Record an observation for the current label set."""

            self._histogram._observe(self._labels, value)

    class _Histogram:
        """Minimal histogram implementation emitting Prometheus text format."""

        def __init__(
            self,
            name: str,
            documentation: str,
            labelnames: Iterable[str],
            buckets: Iterable[float],
        ) -> None:
            self.name = name
            self.documentation = documentation
            self.labelnames = tuple(labelnames)
            self.buckets = tuple(buckets)
            self._samples: dict[tuple[str, ...], list[float]] = defaultdict(list)
            _FALLBACK_REGISTRY.append(self)

        def labels(self, **kwargs: str) -> _HistogramChild:
            """Return a child collector bound to the provided labels."""

            label_values = tuple(kwargs[label] for label in self.labelnames)
            return _HistogramChild(self, label_values)

        def _observe(self, labels: tuple[str, ...], value: float) -> None:
            self._samples[labels].append(value)

    def _format_labels(labelnames: tuple[str, ...], values: tuple[str, ...]) -> str:
        return ",".join(f'{name}="{value}"' for name, value in zip(labelnames, values))

    def generate_latest() -> bytes:
        """Render collected metrics in Prometheus text exposition format."""

        lines: list[str] = []
        for histogram in _FALLBACK_REGISTRY:
            lines.append(f"# HELP {histogram.name} {histogram.documentation}")
            lines.append(f"# TYPE {histogram.name} histogram")
            for labels, observations in histogram._samples.items():
                label_str = _format_labels(histogram.labelnames, labels)
                total = len(observations)
                for bucket in histogram.buckets:
                    count = sum(1 for value in observations if value <= bucket)
                    lines.append(
                        f"{histogram.name}_bucket{{{label_str},le=\"{bucket}\"}} {count}"
                    )
                lines.append(f"{histogram.name}_bucket{{{label_str},le=\"+Inf\"}} {total}")
                sum_value = sum(observations)
                lines.append(f"{histogram.name}_sum{{{label_str}}} {sum_value}")
                lines.append(f"{histogram.name}_count{{{label_str}}} {total}")
        return "\n".join(lines).encode()

    Histogram = _Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


REQUEST_LATENCY = Histogram(
    "app_request_latency_seconds",
    "Request latency in seconds by method, path, and status code.",
    labelnames=("method", "path", "status_code"),
    buckets=(
        0.005,
        0.01,
        0.025,
        0.05,
        0.1,
        0.25,
        0.5,
        1,
        2.5,
        5,
        10,
    ),
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Record request latency metrics for each processed request."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Measure the response time of the wrapped endpoint."""

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration = time.perf_counter() - start_time
            path_template = _resolve_path_template(request)
            REQUEST_LATENCY.labels(
                method=request.method,
                path=path_template,
                status_code="500",
            ).observe(duration)
            raise
        duration = time.perf_counter() - start_time
        path_template = _resolve_path_template(request)
        REQUEST_LATENCY.labels(
            method=request.method,
            path=path_template,
            status_code=str(response.status_code),
        ).observe(duration)
        return response


def render_metrics() -> Response:
    """Return a Response containing the latest Prometheus metrics."""

    payload = generate_latest()
    return Response(content=payload, media_type=CONTENT_TYPE_LATEST)


def _resolve_path_template(request: Request) -> str:
    """Return the Starlette route template associated with the request."""

    scope = request.scope
    route: Any | None = scope.get("route")
    if route is None:
        return scope.get("path", "unknown")
    path_template = getattr(route, "path", None)
    if not isinstance(path_template, str):
        return scope.get("path", "unknown")
    return path_template
