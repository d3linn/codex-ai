from __future__ import annotations

from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.models.database import get_session
from app.models.schemas import TaskCreate, TaskRead, TaskUpdate
from app.models.task import Task
from app.models.user import User
from app.services.tasks import create_task, delete_task, get_task, list_tasks, update_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[TaskRead])
async def read_tasks(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[TaskRead]:
    return await list_tasks(session, current_user)


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task_endpoint(
    task_in: TaskCreate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TaskRead:
    return await create_task(session, current_user, task_in)


@router.get("/{task_id}", response_model=TaskRead)
async def read_task(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TaskRead:
    task: Task | None = await get_task(session, task_id)
    if task is None or task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return cast(TaskRead, TaskRead.model_validate(task))


@router.put("/{task_id}", response_model=TaskRead)
async def update_task_endpoint(
    task_id: int,
    task_in: TaskUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TaskRead:
    task: Task | None = await get_task(session, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    return await update_task(session, task, task_in)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_endpoint(
    task_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    task: Task | None = await get_task(session, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions")
    await delete_task(session, task)
