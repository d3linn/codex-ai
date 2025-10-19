from __future__ import annotations

from fastapi import FastAPI

from app.models.database import Base, engine
from app.routers import auth, health, tasks, users

app = FastAPI()


@app.on_event("startup")
async def on_startup() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(health.router)
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(users.router)
app.include_router(tasks.router)
