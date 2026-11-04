import pytest
from fastapi.testclient import TestClient

from app import db
from app.main import app

client = TestClient(app)


@pytest.fixture
def database_available(request):
    app.dependency_overrides[db.database_is_available] = lambda: request.param
    yield
    app.dependency_overrides.clear()


@pytest.mark.parametrize("database_available", [True], indirect=True)
def test_health_returns_ok_when_database_is_available(database_available):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@pytest.mark.parametrize("database_available", [False], indirect=True)
def test_health_returns_503_when_database_is_unavailable(database_available):
    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}


def test_database_is_unavailable_without_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db.get_engine.cache_clear()

    assert db.database_is_available() is False
