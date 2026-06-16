"""SQLAlchemy database configuration.

For Aula 3 we keep configuration deliberately simple: the database URL comes
from the environment and defaults to the Docker Compose PostgreSQL service.
In Aula 4 this will move to a dedicated settings object based on `.env`.
"""

from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://cloudtask:cloudtask@db:5432/cloudtask",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Base class used by all SQLAlchemy ORM models."""


def get_db() -> Generator[Session, None, None]:
    """Provide one database session per HTTP request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

