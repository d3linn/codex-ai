from __future__ import annotations

from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.schemas import TaskCreate, TaskRead, TaskUpdate
from app.models.task import Task
from app.models.user import User


logger = get_logger(name=__name__)


async def list_tasks(session: AsyncSession, user: User) -> list[TaskRead]:
    """Return tasks for the specified user.

    Args:
        session: Database session used for retrieval.
        user: Owner of the tasks to query.

    Returns:
        list[TaskRead]: Serialized tasks belonging to the user.
    """
    result = await session.scalars(select(Task).where(Task.user_id == user.id))
    tasks = result.all()
    serialized = [cast(TaskRead, TaskRead.model_validate(task)) for task in tasks]
    logger.info("list_tasks", user_id=user.id, task_count=len(serialized))
    return serialized


async def get_task(session: AsyncSession, task_id: int) -> Task | None:
    """Fetch a task by identifier.

    Args:
        session: Database session used for retrieval.
        task_id: Primary key of the task.

    Returns:
        Task | None: The matching task or ``None`` if absent.
    """
    task = await session.get(Task, task_id)
    logger.info("get_task", task_id=task_id, found=task is not None)
    return cast(Task | None, task)


async def create_task(session: AsyncSession, user: User, task_in: TaskCreate) -> TaskRead:
    """Create and persist a new task for a user.

    Args:
        session: Database session used for persistence.
        user: Owner of the new task.
        task_in: Data describing the task.

    Returns:
        TaskRead: Serialized representation of the created task.
    """
    task = Task(
        title=task_in.title,
        description=task_in.description,
        completed=task_in.completed,
        user_id=user.id,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)
    logger.info("create_task_success", task_id=task.id, user_id=user.id)
    return cast(TaskRead, TaskRead.model_validate(task))


async def update_task(session: AsyncSession, task: Task, task_in: TaskUpdate) -> TaskRead:
    """Apply updates to an existing task.

    Args:
        session: Database session used for persistence.
        task: Task instance to update.
        task_in: Requested updates for the task.

    Returns:
        TaskRead: Serialized representation of the updated task.
    """
    if task_in.title is not None:
        task.title = task_in.title
    if task_in.description is not None:
        task.description = task_in.description
    if task_in.completed is not None:
        task.completed = task_in.completed
    await session.commit()
    await session.refresh(task)
    logger.info("update_task_success", task_id=task.id)
    return cast(TaskRead, TaskRead.model_validate(task))


async def delete_task(session: AsyncSession, task: Task) -> None:
    """Delete a task from the database.

    Args:
        session: Database session used for persistence.
        task: Task instance to remove.
    """
    await session.delete(task)
    await session.commit()
    logger.info("delete_task_success", task_id=task.id)
