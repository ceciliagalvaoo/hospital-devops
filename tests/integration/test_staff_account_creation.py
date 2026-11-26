"""Integration tests for staff account creation and case-insensitive logins (T-14.1).

Synthetic data only. The acceptance and access tests of US-14 are T-14.3 (#17).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text

from app.access import NOT_AUTHENTICATED, NOT_PERMITTED
from app.accounts import MESSAGES, AccountDetails, InvalidAccount, create_account
from app.db import get_session
from app.main import app
from app.models import Role, StaffAccount
from tests.csrf import csrf_headers

PASSWORD = "synthetic-password"
NEW_PASSWORD = "synthetic-new-password"


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
    return client.post("/auth/login", data=data, headers=csrf_headers(client))


def create(client, data: dict):
    return client.post("/api/staff", data=data, headers=csrf_headers(client))


def account_count(db_session) -> int:
    return db_session.scalar(select(func.count()).select_from(StaffAccount))


@pytest.fixture
def administrator(client, db_session):
    account(db_session, "synthetic.administrator", Role.ADMINISTRATOR)
    assert log_in(client, "synthetic.administrator").status_code == 200


@pytest.mark.parametrize("role", list(Role))
def test_administrators_create_an_account_that_logs_in_with_its_role(
    client, db_session, administrator, role
):
    response = create(
        client, {"login": f"New.{role.value}", "role": role.value, "password": NEW_PASSWORD}
    )

    assert response.status_code == 201
    assert response.json() == {"login": f"new.{role.value}", "role": role.value, "is_active": True}
    stored = db_session.execute(
        text("SELECT password_hash FROM staff_accounts WHERE login = :login"),
        {"login": f"new.{role.value}"},
    ).scalar_one()
    assert stored.startswith("$2b$12$")
    assert NEW_PASSWORD not in stored
    client.cookies.clear()
    assert log_in(client, f"new.{role.value}", NEW_PASSWORD).json() == {
        "login": f"new.{role.value}",
        "role": role.value,
    }


def test_invalid_data_is_rejected_identified_and_creates_nothing(client, db_session, administrator):
    before = account_count(db_session)

    response = create(client, {"login": "x", "role": "patient", "password": "short"})

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Invalid account data.",
        "errors": {
            "login": MESSAGES["login_invalid"],
            "role": MESSAGES["role_invalid"],
            "password": MESSAGES["password_too_short"],
        },
    }
    assert account_count(db_session) == before


@pytest.mark.parametrize(
    "login", ["synthetic.receptionist", "Synthetic.Receptionist", " SYNTHETIC.RECEPTIONIST "]
)
def test_a_login_in_use_is_rejected_whatever_its_case(client, db_session, administrator, login):
    account(db_session, "synthetic.receptionist", Role.RECEPTIONIST)
    before = account_count(db_session)

    response = create(client, {"login": login, "role": "doctor", "password": NEW_PASSWORD})

    assert response.status_code == 422
    assert response.json()["errors"] == {"login": MESSAGES["login_taken"]}
    assert account_count(db_session) == before


def test_a_login_taken_between_the_check_and_the_insert_is_reported(db_session):
    account(db_session, "synthetic.doctor", Role.DOCTOR)

    with pytest.raises(InvalidAccount) as raised:
        create_account(db_session, AccountDetails("synthetic.doctor", Role.DOCTOR, NEW_PASSWORD))

    assert raised.value.errors == {"login": MESSAGES["login_taken"]}
    assert db_session.scalar(select(func.count()).select_from(StaffAccount)) == 1


@pytest.mark.parametrize("typed", ["Synthetic.Doctor", "SYNTHETIC.DOCTOR", " synthetic.doctor "])
def test_logins_are_not_case_sensitive(client, db_session, typed):
    account(db_session, "synthetic.doctor", Role.DOCTOR)

    response = log_in(client, typed)

    assert (response.status_code, response.json()["login"]) == (200, "synthetic.doctor")


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR])
def test_receptionists_and_doctors_are_refused(client, db_session, role):
    account(db_session, f"synthetic.{role.value}", role)
    log_in(client, f"synthetic.{role.value}")
    before = account_count(db_session)

    response = create(client, {"login": "new.account", "role": "doctor", "password": NEW_PASSWORD})

    assert (response.status_code, response.json()) == (403, {"detail": NOT_PERMITTED})
    assert account_count(db_session) == before


def test_creation_needs_a_session(client, db_session):
    response = create(client, {"login": "new.account", "role": "doctor", "password": NEW_PASSWORD})

    assert (response.status_code, response.json()) == (401, {"detail": NOT_AUTHENTICATED})
    assert account_count(db_session) == 0
