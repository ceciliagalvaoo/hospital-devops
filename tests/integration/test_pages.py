"""Integration tests for the login pages, the role-based navigation and browser errors."""

import re

import pytest
from fastapi.testclient import TestClient

from app.auth import SESSION_COOKIE_NAME
from app.csrf import CSRF_COOKIE_NAME
from app.db import get_session
from app.main import app
from app.models import Role, StaffAccount

PASSWORD = "synthetic-password"
HTML = {"Accept": "text/html,application/xhtml+xml"}
INVALID = "Invalid login or password."

# Expected areas per role, written out from the RBAC matrix (README §3.2) rather than
# read from app.navigation, so that a wrong table in the code makes these tests fail.
ALLOWED = {
    Role.RECEPTIONIST: ["/patients", "/appointments"],
    Role.DOCTOR: ["/appointments", "/records"],
    Role.ADMINISTRATOR: ["/patients", "/doctors", "/appointments", "/staff"],
}
AREA_PATHS = ["/patients", "/doctors", "/appointments", "/records", "/staff"]
ACCESS_CASES = [(path, role) for path in AREA_PATHS for role in Role]


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app, headers=HTML) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def accounts(db_session) -> dict[Role, StaffAccount]:
    created = {}
    for role in Role:
        staff = StaffAccount(login=f"synthetic.{role.value}", role=role)
        staff.set_password(PASSWORD)
        db_session.add(staff)
        created[role] = staff
    db_session.commit()
    return created


def form_token(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, "page has no CSRF field"
    return match.group(1)


def submit_login(client, login: str, password: str = PASSWORD):
    token = form_token(client.get("/login").text)
    return client.post(
        "/login",
        data={"login": login, "password": password, "csrf_token": token},
        follow_redirects=False,
    )


def log_in_as(client, role: Role) -> None:
    assert submit_login(client, f"synthetic.{role.value}").status_code == 303


def nav_links(html: str) -> list[str]:
    nav = re.search(r'<nav aria-label="Main">(.*?)</nav>', html, re.S)
    assert nav, "page has no main navigation"
    return re.findall(r'href="([^"]+)"', nav.group(1))


def test_login_page_has_a_labelled_form_with_a_csrf_token(client):
    response = client.get("/login")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert '<label for="login">' in response.text
    assert '<label for="password">' in response.text
    assert 'autocomplete="current-password"' in response.text
    assert form_token(response.text)
    assert CSRF_COOKIE_NAME in response.cookies


def test_valid_login_redirects_to_the_home_page_of_the_account(client, accounts):
    response = submit_login(client, "synthetic.doctor")

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert SESSION_COOKIE_NAME in response.cookies
    home = client.get("/")
    assert home.status_code == 200
    assert "synthetic.doctor (doctor)" in home.text


@pytest.mark.parametrize(
    ("login", "password"),
    [
        ("synthetic.doctor", "wrong-password"),
        ("synthetic.unknown", PASSWORD),
        ("", ""),
    ],
    ids=["wrong-password", "unknown-login", "empty"],
)
def test_invalid_credentials_show_the_same_error_with_401(client, accounts, login, password):
    response = submit_login(client, login, password)

    assert response.status_code == 401
    assert f'<p class="message error" role="alert">{INVALID}</p>' in response.text
    assert SESSION_COOKIE_NAME not in response.cookies
    assert password not in response.text or password == ""


def test_inactive_account_sees_the_same_error(client, accounts, db_session):
    accounts[Role.DOCTOR].is_active = False
    db_session.commit()

    response = submit_login(client, "synthetic.doctor")

    assert response.status_code == 401
    assert INVALID in response.text


def test_entered_login_is_kept_and_escaped(client, accounts):
    response = submit_login(client, '<script>alert("x")</script>', "wrong")

    assert 'value="&lt;script&gt;alert(&#34;x&#34;)&lt;/script&gt;"' in response.text
    assert "<script>alert" not in response.text


def test_login_form_without_csrf_token_shows_the_error_page(client, accounts):
    client.get("/login")

    response = client.post("/login", data={"login": "synthetic.doctor", "password": PASSWORD})

    assert response.status_code == 403
    assert "The form has expired" in response.text
    assert SESSION_COOKIE_NAME not in response.cookies


def test_login_page_redirects_when_already_logged_in(client, accounts):
    log_in_as(client, Role.RECEPTIONIST)

    response = client.get("/login", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/"


@pytest.mark.parametrize("role", list(Role), ids=str)
def test_navigation_shows_exactly_the_areas_of_the_role(client, accounts, role):
    log_in_as(client, role)

    home = client.get("/")

    assert nav_links(home.text) == ["/", *ALLOWED[role]]
    assert f"({role.value})" in home.text


@pytest.mark.parametrize(("path", "role"), ACCESS_CASES, ids=str)
def test_area_pages_follow_the_rbac_matrix(client, accounts, path, role):
    log_in_as(client, role)

    response = client.get(path)

    if path in ALLOWED[role]:
        assert response.status_code == 200
        assert "under construction" in response.text
    else:
        assert response.status_code == 403
        assert "Access denied" in response.text
        assert "Your role does not have access to this page." in response.text
        assert nav_links(response.text) == ["/", *ALLOWED[role]]


@pytest.mark.parametrize("path", ["/", *AREA_PATHS])
def test_pages_without_a_session_show_the_login_page_with_401(client, path):
    response = client.get(path)

    assert response.status_code == 401
    assert "Please log in to continue." in response.text
    assert form_token(response.text)


def test_api_clients_keep_json_responses(client, accounts):
    api = {"Accept": "application/json"}

    assert client.get("/patients", headers=api).json() == {"detail": "Not authenticated."}
    log_in_as(client, Role.DOCTOR)
    denied = client.get("/patients", headers=api)
    assert denied.status_code == 403
    assert denied.json() == {"detail": "Not permitted for this role."}


def test_logout_form_ends_the_session(client, accounts):
    log_in_as(client, Role.ADMINISTRATOR)
    token = form_token(client.get("/").text)

    response = client.post("/logout", data={"csrf_token": token}, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"
    assert f'{SESSION_COOKIE_NAME}=""' in response.headers["set-cookie"]
    assert client.get("/").status_code == 401


def test_logout_without_session_redirects_to_the_login_page(client):
    token = form_token(client.get("/login").text)

    response = client.post("/logout", data={"csrf_token": token}, follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_unknown_page_shows_the_error_page(client):
    response = client.get("/no-such-page")

    assert response.status_code == 404
    assert "This page does not exist." in response.text
    assert client.get("/no-such-page", headers={"Accept": "*/*"}).json() == {"detail": "Not Found"}


def test_stylesheet_is_served(client):
    response = client.get("/static/styles.css")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")


def test_pages_use_the_configured_database_session(app_uses_test_database):
    # No dependency override: the page goes through app.db.get_session.
    assert TestClient(app, headers=HTML).get("/").status_code == 401
