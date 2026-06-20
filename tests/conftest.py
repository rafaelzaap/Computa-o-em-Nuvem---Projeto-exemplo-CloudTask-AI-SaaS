from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.database import Base, engine, get_db
from app.main import app


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    """Run each test in a transaction that is always rolled back."""
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    connection.execute(text("TRUNCATE TABLE tasks RESTART IDENTITY CASCADE"))
    session = Session(bind=connection, join_transaction_mode="create_savepoint")

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session, tmp_path) -> Generator[TestClient, None, None]:
    """Provide an API client with isolated database and local uploads."""
    settings = get_settings()
    original_mode = settings.storage_mode
    original_directory = settings.local_uploads_dir
    settings.storage_mode = "local"
    settings.local_uploads_dir = str(tmp_path / "uploads")

    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        settings.storage_mode = original_mode
        settings.local_uploads_dir = original_directory
