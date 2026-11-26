"""Acceptance and access tests of US-14, create staff accounts (T-14.3, #17).

Every case runs through both ways of creating an account: the JSON API (`POST /api/staff`)
and the creation page (`POST /staff/new`). Synthetic data only.
"""

import re
from html import unescape

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text

from app.access import NOT_AUTHENTICATED, NOT_PERMITTED
from app.accounts import MESSAGES
from app.db import get_session
from app.main import app
from app.models import Role, StaffAccount
from tests.csrf import csrf_headers

PASSWORD = "synthetic-password"
NEW_PASSWORD = "synthetic-new-password"
HTML = {"Accept": "text/html"}
JSON = {"Accept": "application/json"}
CHANNELS = ["api", "page"]


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


def account(db_session, login: str, role: Role) -> StaffAccount:
    staff = StaffAccount(login=login, role=role)
    staff.set_password(PASSWORD)
    db_session.add(staff)
    db_session.commit()
    return staff


def log_in(client, login: str, password: str = PASSWORD):
    data = {"login": login, "password": password}
    return client.post("/auth/login", data=data, headers=csrf_headers(client) | JSON)


def log_in_as(client, db_session, role: Role) -> StaffAccount:
    staff = account(db_session, f"synthetic.login.{role.value}", role)
    assert log_in(client, staff.login).status_code == 200
    return staff


def create(client, channel: str, login: str, role: str, password: str = NEW_PASSWORD):
    """Create through the API or the page; return the response and the field errors."""
    data = {"login": login, "role": role, "password": password}
    headers = csrf_headers(client)
    if channel == "api":
        response = client.post("/api/staff", data=data, headers=headers | JSON)
        errors = response.json().get("errors", {}) if response.status_code == 422 else {}
        return response, errors
    response = client.post(
        "/staff/new",
        data=data | {"password_confirmation": password},
        headers=headers | HTML,
        follow_redirects=False,
    )
    found = re.findall(r'<p class="field-error" id="(\w+)-error">(.*?)</p>', response.text)
    return response, {field: unescape(message) for field, message in found}


def stored_hash(db_session, login: str) -> str | None:
    return db_session.execute(
        text("SELECT password_hash FROM staff_accounts WHERE login = :login"), {"login": login}
    ).scalar_one_or_none()


def account_count(db_session) -> int:
    return db_session.scalar(select(func.count()).select_from(StaffAccount))


# ---------------------------------------------------------------- criterion 1: created and usable


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize("role", list(Role))
def test_a_new_account_has_a_bcrypt_hash_and_logs_in_with_its_role(
    client, db_session, channel, role
):
    log_in_as(client, db_session, Role.ADMINISTRATOR)

    response, errors = create(client, channel, f"new.{role.value}", role.value)

    assert errors == {}
    assert response.status_code == (201 if channel == "api" else 303)
    stored = stored_hash(db_session, f"new.{role.value}")
    assert stored.startswith("$2b$12$")  # bcrypt with cost factor 12 (NFR-03: at least 10)
    assert NEW_PASSWORD not in stored
    client.cookies.clear()
    signed_in = log_in(client, f"new.{role.value}", NEW_PASSWORD)
    assert (signed_in.status_code, signed_in.json()) == (
        200,
        {"login": f"new.{role.value}", "role": role.value},
    )


@pytest.mark.parametrize("channel", CHANNELS)
def test_the_new_account_sees_the_areas_of_its_role(client, db_session, channel):
    log_in_as(client, db_session, Role.ADMINISTRATOR)
    create(client, channel, "new.doctor", "doctor")
    client.cookies.clear()
    log_in(client, "new.doctor", NEW_PASSWORD)

    assert client.get("/records", headers=HTML).status_code == 200
    assert client.get("/staff", headers=HTML).status_code == 403


# ---------------------------------------------------------------- criterion 2: duplicates and roles


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize(
    "login", ["synthetic.receptionist", "Synthetic.Receptionist", "SYNTHETIC.RECEPTIONIST"]
)
def test_a_duplicate_login_is_rejected_in_any_case(client, db_session, channel, login):
    log_in_as(client, db_session, Role.ADMINISTRATOR)
    existing = account(db_session, "synthetic.receptionist", Role.RECEPTIONIST)
    before = account_count(db_session)

    response, errors = create(client, channel, login, "doctor")

    assert response.status_code == 422
    assert errors == {"login": MESSAGES["login_taken"]}
    assert account_count(db_session) == before
    db_session.expire_all()
    assert existing.role is Role.RECEPTIONIST  # the existing account is unchanged
    assert existing.check_password(PASSWORD)


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize("role", ["", "patient", "nurse", "Administrator", "root"])
def test_an_unsupported_role_is_rejected(client, db_session, channel, role):
    log_in_as(client, db_session, Role.ADMINISTRATOR)
    before = account_count(db_session)

    response, errors = create(client, channel, "new.account", role)

    assert response.status_code == 422
    assert errors == {"role": MESSAGES["role_invalid"]}
    assert account_count(db_session) == before


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize(
    ("login", "password", "expected"),
    [
        ("", NEW_PASSWORD, {"login": "login_missing"}),
        ("x", NEW_PASSWORD, {"login": "login_invalid"}),
        ("with space", NEW_PASSWORD, {"login": "login_invalid"}),
        ("new.account", "", {"password": "password_missing"}),
        ("new.account", "x" * 11, {"password": "password_too_short"}),
    ],
    ids=["no-login", "short-login", "space", "no-password", "short-password"],
)
def test_invalid_logins_and_passwords_are_rejected(
    client, db_session, channel, login, password, expected
):
    log_in_as(client, db_session, Role.ADMINISTRATOR)
    before = account_count(db_session)

    response, errors = create(client, channel, login, "doctor", password)

    assert response.status_code == 422
    assert errors == {field: MESSAGES[key] for field, key in expected.items()}
    assert account_count(db_session) == before


# ---------------------------------------------------------------- criterion 3: access is refused


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR])
def test_receptionists_and_doctors_are_refused(client, db_session, channel, role):
    log_in_as(client, db_session, role)
    before = account_count(db_session)

    response, _ = create(client, channel, "new.account", "administrator")

    assert response.status_code == 403
    if channel == "api":
        assert response.json() == {"detail": NOT_PERMITTED}
    else:
        assert "Access denied" in response.text
    assert account_count(db_session) == before
    assert stored_hash(db_session, "new.account") is None


@pytest.mark.parametrize("channel", CHANNELS)
def test_creation_without_a_session_is_refused(client, db_session, channel):
    response, _ = create(client, channel, "new.account", "administrator")

    assert response.status_code == 401
    if channel == "api":
        assert response.json() == {"detail": NOT_AUTHENTICATED}
    else:
        assert "Please log in to continue." in response.text
    assert account_count(db_session) == 0


def test_a_deactivated_administrator_can_no_longer_create_accounts(client, db_session):
    administrator = log_in_as(client, db_session, Role.ADMINISTRATOR)
    administrator.is_active = False
    db_session.commit()

    response, _ = create(client, "api", "new.account", "doctor")

    assert response.status_code == 401
    assert stored_hash(db_session, "new.account") is None
