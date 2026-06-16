"""Pydantic schemas for task input and output."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.db.models import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    """Fields shared by task create, update and read schemas."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=120,
        description="Short task title.",
        examples=["Preparar deploy no ECS"],
    )
    description: str | None = Field(
        default=None,
        description="Optional details about the task.",
        examples=["Validar variaveis de ambiente antes do deploy."],
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Current workflow state.",
        examples=[TaskStatus.PENDING],
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="Relative priority of the task.",
        examples=[TaskPriority.MEDIUM],
    )

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("title cannot be blank")
        return stripped


class TaskCreate(TaskBase):
    """Request body used to create a task."""


class TaskUpdate(BaseModel):
    """Request body used to partially update a task."""

    title: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None

    @field_validator("title")
    @classmethod
    def _title_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("title cannot be blank")
        return stripped


class TaskRead(TaskBase):
    """Task representation returned by the API."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
