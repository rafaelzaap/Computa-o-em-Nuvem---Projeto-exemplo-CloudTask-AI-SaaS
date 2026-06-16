"""CRUD routes for tasks.

These endpoints are the first part of the app that persists data. They use a
PostgreSQL database locally via Docker Compose, mirroring the role that Amazon
RDS can play in a cloud deployment.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Task
from app.db.schemas import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Criar tarefa",
)
def create_task(payload: TaskCreate, db: DbSession) -> Task:
    """Create a task and persist it in PostgreSQL."""
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get(
    "",
    response_model=list[TaskRead],
    summary="Listar tarefas",
)
def list_tasks(
    db: DbSession,
    skip: Annotated[int, Query(ge=0, description="How many rows to skip.")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum rows to return.")] = 50,
) -> list[Task]:
    """List tasks ordered by newest first."""
    statement = select(Task).order_by(Task.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(statement).all())


@router.get(
    "/{task_id}",
    response_model=TaskRead,
    summary="Buscar tarefa por ID",
)
def get_task(task_id: int, db: DbSession) -> Task:
    """Return one task or 404 when it does not exist."""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )
    return task


@router.put(
    "/{task_id}",
    response_model=TaskRead,
    summary="Atualizar tarefa",
)
def update_task(task_id: int, payload: TaskUpdate, db: DbSession) -> Task:
    """Partially update a task."""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remover tarefa",
)
def delete_task(task_id: int, db: DbSession) -> Response:
    """Delete a task when it exists."""
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    db.delete(task)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
