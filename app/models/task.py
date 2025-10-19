from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, default="")
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    user: Mapped["User"] = relationship(back_populates="tasks")

    def __init__(
        self,
        *,
        title: str,
        description: str,
        completed: bool,
        user_id: int,
    ) -> None:
        """Initialize a task model instance.

        Args:
            title: Short name of the task.
            description: Detailed task description.
            completed: Completion state of the task.
            user_id: Identifier of the owning user.
        """
        self.title = title
        self.description = description
        self.completed = completed
        self.user_id = user_id
