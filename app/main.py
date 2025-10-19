from __future__ import annotations

from fastapi import FastAPI

from app.core.logging import configure_logging
from app.core.metrics import MetricsMiddleware
from app.core.middleware import RequestContextMiddleware
from app.models.database import Base, engine
from app.routers import auth, health, metrics, summary, tasks, users

configure_logging()

app = FastAPI()
app.add_middleware(MetricsMiddleware)
app.add_middleware(RequestContextMiddleware)


@app.on_event("startup")
async def on_startup() -> None:
    """Create database tables on application startup.

    Returns:
        None: This function is executed for its side effects only.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(health.router)
app.include_router(metrics.router, tags=["metrics"])
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router)
app.include_router(tasks.router)
app.include_router(summary.router)
