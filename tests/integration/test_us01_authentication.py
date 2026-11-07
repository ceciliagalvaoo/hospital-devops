"""US-01 authentication cases not covered by the per-feature test modules (T-01.6, #10).

The full map of US-01 cases to tests is in docs/testing/us-01-automated-tests.md.
"""

import re
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app import security, seed
from app.auth import SESSION_LIFETIME
from app.csrf import CSRF_HEADER, INVALID_TOKEN
from app.db import get_session
from app.main import app
from app.models import Role, StaffAccount, StaffSession
from app.security import MAX_PASSWORD_BYTES
from tests.csrf import csrf_headers

PASSWORD = "synthetic-password"
HTML = {"Accept": "text/html"}

# Every state-changing route of the application. A new POST route must be added here
# (test_every_state_changing_route_is_listed fails otherwise).
STATE_CHANGING_ROUTES = [
    ("POST", "/auth/login"),
    ("POST", "/auth/logout"),
    ("POST", "/login"),
    ("POST", "/logout"),
]


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def account(db_session):
    staff = StaffAccount(login="synthetic.administrator", role=Role.ADMINISTRATOR)
    staff.set_password(PASSWORD)
    db_session.add(staff)
    db_session.commit()
    return staff


def api_login(client, login: str, password: str):
    return client.post(
        "/auth/login", data={"login": login, "password": password}, headers=csrf_headers(client)
    )


@pytest.mark.parametrize("login", ["synthetic.unknown", "synthetic.administrator"])
def test_every_login_attempt_runs_one_bcrypt_check(client, account, monkeypatch, login):
    # Unknown logins are checked against a dummy hash, so the response time does not
    # reveal whether a login exists.
    calls = []
    checkpw = security.bcrypt.checkpw
    monkeypatch.setattr(
        security.bcrypt, "checkpw", lambda *args: calls.append(args) or checkpw(*args)
    )

    response = api_login(client, login, "wrong-password")

    assert response.status_code == 401
    assert len(calls) == 1


# Written out instead of read from app.seed, so a wrong role in the seed fails the test.
SEEDED_ROLES = [
    ("dev.receptionist", "receptionist"),
    ("dev.doctor", "doctor"),
    ("dev.administrator", "administrator"),
]


@pytest.mark.parametrize(("login", "role"), SEEDED_ROLES)
def test_seeded_development_accounts_can_log_in_with_their_role(client, db_session, login, role):
    seed.seed_staff_accounts(db_session, PASSWORD)
    db_session.commit()

    response = api_login(client, login, PASSWORD)

    assert response.status_code == 200
    assert response.json() == {"login": login, "role": role}


@pytest.mark.parametrize(
    "password",
    ["x" * (MAX_PASSWORD_BYTES + 1), "é" * (MAX_PASSWORD_BYTES // 2 + 1)],
    ids=["ascii", "multibyte"],
)
def test_password_longer_than_72_bytes_is_refused_with_401(client, account, password):
    response = api_login(client, "synthetic.administrator", password)

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid login or password."}


def test_new_session_expires_after_eight_hours(client, account, db_session):
    before = datetime.now(UTC)
    api_login(client, "synthetic.administrator", PASSWORD)
    after = datetime.now(UTC)

    session = db_session.scalars(select(StaffSession)).one()

    assert before + SESSION_LIFETIME <= session.expires_at <= after + SESSION_LIFETIME
    assert SESSION_LIFETIME.total_seconds() == 8 * 3600


@pytest.mark.parametrize(("method", "path"), STATE_CHANGING_ROUTES)
def test_every_state_changing_route_refuses_requests_without_a_csrf_token(
    client, account, method, path
):
    api_login(client, "synthetic.administrator", PASSWORD)  # logged in, but no token sent

    response = client.request(method, path, data={"login": "x", "password": "y"})

    assert response.status_code == 403
    assert response.json() == {"detail": INVALID_TOKEN}
    assert client.get("/auth/me").status_code == 200  # the session was not ended


@pytest.mark.parametrize(("method", "path"), STATE_CHANGING_ROUTES)
def test_every_state_changing_route_accepts_a_valid_token(client, account, method, path):
    response = client.request(
        method,
        path,
        data={"login": "synthetic.administrator", "password": PASSWORD},
        headers=csrf_headers(client),
        follow_redirects=False,
    )

    assert response.status_code in {200, 204, 303}


def test_every_state_changing_route_is_listed():
    # Reads the OpenAPI schema plus the page routes, which are hidden from it.
    listed = {(method, path) for method, path in STATE_CHANGING_ROUTES}
    openapi = {
        (method.upper(), path)
        for path, operations in app.openapi()["paths"].items()
        for method in operations
        if method.upper() not in {"GET", "HEAD", "OPTIONS"}
    }
    pages = {
        (method, path)
        for path, methods in _page_routes().items()
        for method in methods
        if method not in {"GET", "HEAD", "OPTIONS"}
    }

    assert openapi | pages == listed


def _page_routes() -> dict[str, set[str]]:
    from app.routes import pages

    return {route.path: set(route.methods) for route in pages.router.routes}


def test_page_logout_without_token_keeps_the_session(client, account):
    api_login(client, "synthetic.administrator", PASSWORD)

    response = client.post("/logout", headers=HTML, follow_redirects=False)

    assert response.status_code == 403
    assert "The form has expired" in response.text
    assert client.get("/auth/me").status_code == 200


def test_csrf_token_from_a_page_form_matches_the_api_token(client, account):
    api_login(client, "synthetic.administrator", PASSWORD)

    page_token = re.search(r'name="csrf_token" value="([^"]+)"', client.get("/", headers=HTML).text)

    assert page_token and page_token.group(1) == csrf_headers(client)[CSRF_HEADER]
