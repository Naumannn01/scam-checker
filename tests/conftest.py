import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app import models  # noqa: F401  (registers every table on Base.metadata)
from app.limiter import limiter
from app.main import app


@pytest.fixture()
def db_session():
    # StaticPool + check_same_thread=False so every connection shares
    # the same in-memory database
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture()
def mock_task(monkeypatch):
    """Replace the Celery task so .delay() is recorded but never hits Redis."""
    mock = MagicMock()
    monkeypatch.setattr("app.routers.check.check_domain_whois", mock)
    return mock


@pytest.fixture()
def client(db_session, mock_task):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    limiter.enabled = False
    with TestClient(app) as c:
        yield c
    limiter.enabled = True
    app.dependency_overrides.clear()