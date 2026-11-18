"""The interactive API documentation is served only in development (T-01.13, #225)."""

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

DOC_PATHS = ["/docs", "/redoc", "/openapi.json"]


@pytest.mark.parametrize("path", DOC_PATHS)
def test_api_documentation_is_served_in_development(monkeypatch, path):
    monkeypatch.setenv("APP_ENV", "development")

    response = TestClient(create_app()).get(path)

    assert response.status_code == 200


@pytest.mark.parametrize("app_env", [None, "production", "test", "Development"])
@pytest.mark.parametrize("path", DOC_PATHS)
def test_api_documentation_is_not_served_outside_development(monkeypatch, app_env, path):
    if app_env is None:
        monkeypatch.delenv("APP_ENV", raising=False)
    else:
        monkeypatch.setenv("APP_ENV", app_env)

    response = TestClient(create_app()).get(path, headers={"Accept": "application/json"})

    assert response.status_code == 404


def test_application_routes_work_without_the_documentation(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")

    response = TestClient(create_app()).get("/auth/csrf")  # a route that needs no database

    assert response.status_code == 200
    assert response.json()["csrf_token"]
    assert response.headers["cache-control"] == "no-store"
