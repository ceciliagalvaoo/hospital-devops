"""Integration tests for staff account deactivation through the API (T-15.1). Synthetic data
only. The acceptance and access tests of US-15, over the API and the pages, are T-15.3 (#22).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.access import NOT_AUTHENTICATED, NOT_PERMITTED
from app.accounts import OWN_ACCOUNT
from app.db import get_session
from app.main import app
from app.models import Role, StaffAccount, StaffSession
from tests.csrf import csrf_headers

PASSWORD = "synthetic-password"


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


def other_client():
    """A second browser, for the sessions of another account."""
    return TestClient(app)


def account(db_session, login: str, role: Role = Role.RECEPTIONIST) -> StaffAccount:
    staff = StaffAccount(login=login, role=role)
    staff.set_password(PASSWORD)
    db_session.add(staff)
    db_session.commit()
    return staff


def log_in(client, login: str):
    data = {"login": login, "password": PASSWORD}
    return client.post("/auth/login", data=data, headers=csrf_headers(client))


def deactivate(client, account_id: int):
    return client.post(f"/api/staff/{account_id}/deactivate", headers=csrf_headers(client))


def sessions_of(db_session, staff: StaffAccount) -> int:
    return db_session.scalar(
        select(func.count())
        .select_from(StaffSession)
        .where(StaffSession.staff_account_id == staff.id)
    )


def is_active(db_session, staff: StaffAccount) -> bool:
    db_session.expire_all()
    return staff.is_active


@pytest.fixture
def administrator(client, db_session) -> StaffAccount:
    staff = account(db_session, "synthetic.administrator", Role.ADMINISTRATOR)
    assert log_in(client, staff.login).status_code == 200
    return staff


def test_administrators_deactivate_an_account_and_end_its_sessions(
    client, db_session, administrator
):
    target = account(db_session, "synthetic.receptionist")
    with other_client() as browser:
        assert log_in(browser, target.login).status_code == 200
        assert browser.get("/api/patients?q=synthetic").status_code == 200
        assert sessions_of(db_session, target) == 1

        response = deactivate(client, target.id)

        assert (response.status_code, response.json()) == (
            200,
            {"login": "synthetic.receptionist", "role": "receptionist", "is_active": False},
        )
        assert not is_active(db_session, target)
        assert sessions_of(db_session, target) == 0  # deleted, not only refused
        # The existing session is rejected, and a new login is refused.
        assert browser.get("/api/patients?q=synthetic").status_code == 401
        assert log_in(browser, target.login).status_code == 401
    # The account is kept, never deleted.
    assert db_session.get(StaffAccount, target.id) is not None


def test_other_accounts_keep_their_sessions(client, db_session, administrator):
    target = account(db_session, "synthetic.receptionist")
    other = account(db_session, "synthetic.receptionist.other")
    with other_client() as browser:
        log_in(browser, other.login)

        deactivate(client, target.id)

        assert browser.get("/api/patients?q=synthetic").status_code == 200
    assert is_active(db_session, other)
    assert client.get("/api/patients?q=synthetic").status_code == 200  # nor the administrator


def test_deactivating_an_inactive_account_changes_nothing(client, db_session, administrator):
    target = account(db_session, "synthetic.receptionist")
    deactivate(client, target.id)

    response = deactivate(client, target.id)

    assert (response.status_code, response.json()["is_active"]) == (200, False)


def test_administrators_cannot_deactivate_their_own_account(client, db_session, administrator):
    response = deactivate(client, administrator.id)

    assert (response.status_code, response.json()) == (409, {"detail": OWN_ACCOUNT})
    assert is_active(db_session, administrator)
    assert client.get("/api/patients?q=synthetic").status_code == 200  # still logged in


def test_unknown_accounts_are_not_found(client, administrator):
    assert deactivate(client, 999999).status_code == 404


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR])
def test_receptionists_and_doctors_are_refused(client, db_session, role):
    target = account(db_session, "synthetic.target", Role.DOCTOR)
    account(db_session, f"synthetic.{role.value}.user", role)
    log_in(client, f"synthetic.{role.value}.user")

    response = deactivate(client, target.id)

    assert (response.status_code, response.json()) == (403, {"detail": NOT_PERMITTED})
    assert is_active(db_session, target)


def test_deactivation_needs_a_session(client, db_session):
    target = account(db_session, "synthetic.receptionist")

    response = deactivate(client, target.id)

    assert (response.status_code, response.json()) == (401, {"detail": NOT_AUTHENTICATED})
    assert is_active(db_session, target)
