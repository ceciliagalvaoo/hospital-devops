"""Integration tests for the CSRF protection of state-changing requests."""

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.csrf import (
    CROSS_ORIGIN,
    CSRF_COOKIE_NAME,
    CSRF_FORM_FIELD,
    CSRF_HEADER,
    INVALID_TOKEN,
    csrf_protect,
)
from app.db import get_session
from app.main import app
from app.models import Role, StaffAccount
from tests.csrf import csrf_headers

PASSWORD = "synthetic-password"
CREDENTIALS = {"login": "synthetic.receptionist", "password": PASSWORD}
REFUSED = {"detail": INVALID_TOKEN}
OWN_ORIGIN = "http://testserver"


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def account(db_session):
    staff = StaffAccount(login="synthetic.receptionist", role=Role.RECEPTIONIST)
    staff.set_password(PASSWORD)
    db_session.add(staff)
    db_session.commit()
    return staff


def token(client) -> str:
    return csrf_headers(client)[CSRF_HEADER]


def log_in(client) -> None:
    response = client.post("/auth/login", data=CREDENTIALS, headers=csrf_headers(client))
    assert response.status_code == 200


def test_csrf_endpoint_sets_a_pre_session_cookie_and_returns_a_token(client):
    response = client.get("/auth/csrf")

    assert response.status_code == 200
    assert response.json()["csrf_token"]
    cookie = response.headers["set-cookie"]
    assert cookie.startswith(f"{CSRF_COOKIE_NAME}=")
    assert "HttpOnly" in cookie
    assert "SameSite=lax" in cookie


def test_token_is_stable_until_the_binding_cookie_changes(client):
    first = token(client)

    assert token(client) == first
    assert "set-cookie" not in client.get("/auth/csrf").headers


@pytest.mark.parametrize(("method", "path"), [("POST", "/auth/login"), ("POST", "/auth/logout")])
def test_state_changing_requests_without_a_token_are_refused(client, account, method, path):
    client.get("/auth/csrf")  # the browser has a pre-session cookie, but sends no token

    response = client.request(method, path, data=CREDENTIALS)

    assert response.status_code == 403
    assert response.json() == REFUSED


def test_request_without_any_cookie_is_refused(client, account):
    response = client.post("/auth/login", data=CREDENTIALS, headers={CSRF_HEADER: "anything"})

    assert response.status_code == 403
    assert response.json() == REFUSED


@pytest.mark.parametrize("value", ["wrong-token", "", "tök€n-with-non-ascii"])
def test_wrong_token_is_refused(client, account, value):
    client.get("/auth/csrf")

    # Sent as a form field: HTTP headers cannot carry the non-ASCII value.
    response = client.post("/auth/login", data={**CREDENTIALS, CSRF_FORM_FIELD: value})

    assert response.status_code == 403
    assert response.json() == REFUSED


def test_token_is_accepted_from_the_header(client, account):
    response = client.post("/auth/login", data=CREDENTIALS, headers=csrf_headers(client))

    assert response.status_code == 200


def test_token_is_accepted_from_the_form_field(client, account):
    response = client.post("/auth/login", data={**CREDENTIALS, CSRF_FORM_FIELD: token(client)})

    assert response.status_code == 200


def test_token_issued_before_login_is_refused_after_login(client, account):
    before = token(client)
    log_in(client)

    response = client.post("/auth/logout", headers={CSRF_HEADER: before})

    assert response.status_code == 403
    assert token(client) != before
    assert client.post("/auth/logout", headers=csrf_headers(client)).status_code == 204


def test_token_of_another_session_is_refused(client, account, db_session):
    log_in(client)
    other_token = token(client)
    with TestClient(app) as other_client:
        log_in(other_client)

        response = other_client.post("/auth/logout", headers={CSRF_HEADER: other_token})

    assert response.status_code == 403
    assert response.json() == REFUSED


def test_cross_origin_request_is_refused_even_with_a_valid_token(client, account):
    headers = {**csrf_headers(client), "Origin": "https://attacker.example"}

    response = client.post("/auth/login", data=CREDENTIALS, headers=headers)

    assert response.status_code == 403
    assert response.json() == {"detail": CROSS_ORIGIN}


@pytest.mark.parametrize(
    "headers", [{"Origin": "null"}, {"Sec-Fetch-Site": "cross-site"}], ids=["null", "fetch"]
)
def test_other_cross_site_signals_are_refused(client, account, headers):
    response = client.post(
        "/auth/login", data=CREDENTIALS, headers={**csrf_headers(client), **headers}
    )

    assert response.status_code == 403
    assert response.json() == {"detail": CROSS_ORIGIN}


@pytest.mark.parametrize("site", ["same-origin", "none"])
def test_same_origin_requests_with_a_valid_token_pass(client, account, site):
    headers = {**csrf_headers(client), "Origin": OWN_ORIGIN, "Sec-Fetch-Site": site}

    response = client.post("/auth/login", data=CREDENTIALS, headers=headers)

    assert response.status_code == 200


def test_safe_methods_are_not_checked(client):
    cross_site = {"Origin": "https://attacker.example"}

    assert client.get("/auth/csrf", headers=cross_site).status_code == 200
    assert client.get("/auth/me", headers=cross_site).status_code == 401  # not 403


def test_the_check_applies_to_the_whole_application():
    assert csrf_protect in [dependency.dependency for dependency in app.router.dependencies]


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_every_state_changing_method_is_checked(method):
    guarded = FastAPI(dependencies=[Depends(csrf_protect)])

    @guarded.api_route("/change", methods=[method])
    def change() -> dict[str, str]:
        return {"changed": "yes"}

    response = TestClient(guarded).request(method, "/change")

    assert response.status_code == 403
    assert response.json() == REFUSED
