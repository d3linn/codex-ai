from __future__ import annotations

from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schemas import TaskCreate, TaskRead, TaskUpdate
from app.models.task import Task
from app.models.user import User


async def list_tasks(session: AsyncSession, user: User) -> list[TaskRead]:
    result = await session.scalars(select(Task).where(Task.user_id == user.id))
    tasks = result.all()
    return [cast(TaskRead, TaskRead.model_validate(task)) for task in tasks]


async def get_task(session: AsyncSession, task_id: int) -> Task | None:
    task = await session.get(Task, task_id)
    return cast(Task | None, task)


async def create_task(session: AsyncSession, user: User, task_in: TaskCreate) -> TaskRead:
    task = Task(
        title=task_in.title,
        description=task_in.description,
        completed=task_in.completed,
        user_id=user.id,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return cast(TaskRead, TaskRead.model_validate(task))


async def update_task(session: AsyncSession, task: Task, task_in: TaskUpdate) -> TaskRead:
    if task_in.title is not None:
        task.title = task_in.title
    if task_in.description is not None:
        task.description = task_in.description
    if task_in.completed is not None:
        task.completed = task_in.completed
    await session.commit()
    await session.refresh(task)
    return cast(TaskRead, TaskRead.model_validate(task))


async def delete_task(session: AsyncSession, task: Task) -> None:
    await session.delete(task)
    await session.commit()
