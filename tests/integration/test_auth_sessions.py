"""Integration tests for login, logout and server-side sessions."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.auth import SESSION_COOKIE_NAME, SESSION_LIFETIME, hash_token
from app.db import get_session
from app.main import app
from app.models import Role, StaffAccount, StaffSession
from tests.csrf import csrf_headers

PASSWORD = "synthetic-password"
INVALID = {"detail": "Invalid login or password."}


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def account(db_session):
    staff = StaffAccount(login="synthetic.doctor", role=Role.DOCTOR)
    staff.set_password(PASSWORD)
    db_session.add(staff)
    db_session.commit()
    return staff


def log_in(client, login="synthetic.doctor", password=PASSWORD):
    return client.post(
        "/auth/login", data={"login": login, "password": password}, headers=csrf_headers(client)
    )


def log_out(client):
    return client.post("/auth/logout", headers=csrf_headers(client))


def session_count(db_session) -> int:
    return db_session.scalar(select(func.count()).select_from(StaffSession))


def test_valid_login_creates_session_and_returns_account(client, account, db_session):
    response = log_in(client)

    assert response.status_code == 200
    assert response.json() == {"login": "synthetic.doctor", "role": "doctor"}
    assert session_count(db_session) == 1
    assert client.get("/auth/me").json() == {"login": "synthetic.doctor", "role": "doctor"}


def test_session_cookie_is_http_only_lax_and_limited_in_lifetime(client, account):
    cookie = log_in(client).headers["set-cookie"]

    assert cookie.startswith(f"{SESSION_COOKIE_NAME}=")
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie
    assert f"Max-Age={int(SESSION_LIFETIME.total_seconds())}" in cookie
    assert "Secure" not in cookie


def test_session_cookie_is_secure_when_configured(client, account, monkeypatch):
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "true")
    client.base_url = "https://testserver"  # browsers send Secure cookies only over HTTPS

    assert "Secure" in client.get("/auth/csrf").headers["set-cookie"]
    assert "Secure" in log_in(client).headers["set-cookie"]


@pytest.mark.parametrize(
    ("login", "password"),
    [("synthetic.doctor", "wrong-password"), ("synthetic.unknown", PASSWORD)],
)
def test_invalid_credentials_are_refused_with_the_same_message(
    client, account, db_session, login, password
):
    response = log_in(client, login, password)

    assert response.status_code == 401
    assert response.json() == INVALID
    assert SESSION_COOKIE_NAME not in response.cookies
    assert session_count(db_session) == 0


def test_inactive_account_cannot_log_in(client, account, db_session):
    account.is_active = False
    db_session.commit()

    response = log_in(client)

    assert response.status_code == 401
    assert response.json() == INVALID


def test_only_a_hash_of_the_token_is_stored(client, account, db_session):
    log_in(client)
    token = client.cookies[SESSION_COOKIE_NAME]

    stored = db_session.scalars(select(StaffSession.token_hash)).one()
    assert stored != token
    assert stored == hash_token(token)


def test_each_login_issues_a_new_token_and_replaces_the_old_session(client, account, db_session):
    log_in(client)
    first = client.cookies[SESSION_COOKIE_NAME]
    log_in(client)
    second = client.cookies[SESSION_COOKIE_NAME]

    assert first != second
    assert session_count(db_session) == 1


def test_me_requires_a_session(client):
    response = client.get("/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated."}


def test_logout_deletes_session_and_clears_cookie(client, account, db_session):
    log_in(client)
    token = client.cookies[SESSION_COOKIE_NAME]

    response = log_out(client)

    assert response.status_code == 204
    assert f'{SESSION_COOKIE_NAME}=""' in response.headers["set-cookie"]
    assert session_count(db_session) == 0
    client.cookies.set(SESSION_COOKIE_NAME, token)
    assert client.get("/auth/me").status_code == 401


def test_logout_without_session_succeeds(client):
    assert log_out(client).status_code == 204


def test_expired_session_is_rejected_and_removed(client, account, db_session):
    log_in(client)
    stored = db_session.scalars(select(StaffSession)).one()
    stored.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db_session.commit()

    assert client.get("/auth/me").status_code == 401
    assert session_count(db_session) == 0


def test_session_of_a_deactivated_account_is_rejected(client, account, db_session):
    log_in(client)
    account.is_active = False
    db_session.commit()

    assert client.get("/auth/me").status_code == 401
    assert session_count(db_session) == 0


def test_unknown_token_is_rejected(client, account):
    client.cookies.set(SESSION_COOKIE_NAME, "not-a-real-token")

    assert client.get("/auth/me").status_code == 401


def test_routes_use_the_configured_database_session(app_uses_test_database):
    # No dependency override: the request goes through app.db.get_session.
    assert TestClient(app).get("/auth/me").status_code == 401
