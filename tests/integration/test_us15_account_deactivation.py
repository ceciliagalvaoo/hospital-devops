"""Acceptance and access tests of US-15, deactivate a staff account (T-15.3, #22).

Every deactivation case runs through both ways of deactivating an account: the JSON API
(`POST /api/staff/<id>/deactivate`) and the confirmation page (`POST /staff/<id>/deactivate`).
Logins are tried through the API (`POST /auth/login`) and the login page (`POST /login`), and
existing sessions are used through both the API and the pages. Synthetic data only.
"""

import re
from datetime import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.access import NOT_AUTHENTICATED, NOT_PERMITTED
from app.accounts import OWN_ACCOUNT
from app.db import get_session
from app.main import app
from app.models import (
    AvailabilityRange,
    Doctor,
    Role,
    Specialisation,
    StaffAccount,
    StaffSession,
    Weekday,
)
from app.routes.auth import INVALID_CREDENTIALS
from tests.csrf import csrf_headers

PASSWORD = "synthetic-password"
HTML = {"Accept": "text/html"}
JSON = {"Accept": "application/json"}
CHANNELS = ["api", "page"]
# A protected API request and a protected page that each role may use.
ALLOWED = {
    Role.RECEPTIONIST: ("/api/patients?q=synthetic", "/patients"),
    Role.DOCTOR: ("/auth/me", "/"),
    Role.ADMINISTRATOR: ("/auth/me", "/staff"),
}


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


def browser() -> TestClient:
    """Another browser, with its own cookies, sharing the overridden database session."""
    return TestClient(app)


def account(db_session, login: str, role: Role) -> StaffAccount:
    staff = StaffAccount(login=login, role=role)
    staff.set_password(PASSWORD)
    db_session.add(staff)
    db_session.commit()
    return staff


def log_in(client, login: str, channel: str = "api"):
    if channel == "api":
        data = {"login": login, "password": PASSWORD}
        return client.post("/auth/login", data=data, headers=csrf_headers(client))
    page = client.get("/login", headers=HTML).text
    token = re.search(r'name="csrf_token" value="([^"]+)"', page).group(1)
    data = {"login": login, "password": PASSWORD, "csrf_token": token}
    return client.post("/login", data=data, headers=HTML, follow_redirects=False)


@pytest.fixture
def administrator(client, db_session) -> StaffAccount:
    staff = account(db_session, "synthetic.administrator", Role.ADMINISTRATOR)
    assert log_in(client, staff.login).status_code == 200
    return staff


def deactivate(client, channel: str, account_id: int):
    headers = csrf_headers(client)
    if channel == "api":
        return client.post(f"/api/staff/{account_id}/deactivate", headers=headers | JSON)
    return client.post(
        f"/staff/{account_id}/deactivate", headers=headers | HTML, follow_redirects=False
    )


def is_active(db_session, staff: StaffAccount) -> bool:
    db_session.expire_all()  # read what the database holds
    return staff.is_active


def sessions_of(db_session, staff: StaffAccount) -> int:
    return db_session.scalar(
        select(func.count())
        .select_from(StaffSession)
        .where(StaffSession.staff_account_id == staff.id)
    )


def uses_its_session(session_browser: TestClient, role: Role) -> tuple[int, int]:
    """The status of a protected API request and of a protected page through the session."""
    api, page = ALLOWED[role]
    return (
        session_browser.get(api, headers=JSON).status_code,
        session_browser.get(page, headers=HTML, follow_redirects=False).status_code,
    )


# ---------------------------------------------------------------- criterion 1: refused afterwards


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize("role", list(Role), ids=str)
def test_existing_sessions_are_rejected_after_deactivation(
    client, db_session, administrator, channel, role
):
    target = account(db_session, f"synthetic.{role.value}.target", role)
    with browser() as first, browser() as second:
        assert log_in(first, target.login, "api").status_code == 200
        assert log_in(second, target.login, "page").status_code == 303
        assert uses_its_session(first, role) == (200, 200)
        assert uses_its_session(second, role) == (200, 200)

        response = deactivate(client, channel, target.id)

        assert response.status_code == (200 if channel == "api" else 303)
        assert not is_active(db_session, target)
        # Both sessions are rejected at once, through the API and the pages.
        assert uses_its_session(first, role) == (401, 401)
        assert uses_its_session(second, role) == (401, 401)
        assert first.get(ALLOWED[role][0], headers=JSON).json() == {"detail": NOT_AUTHENTICATED}
        assert "Please log in to continue." in second.get(ALLOWED[role][1], headers=HTML).text
    assert sessions_of(db_session, target) == 0


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize("login_channel", CHANNELS)
def test_later_logins_are_refused_like_wrong_passwords(
    client, db_session, administrator, channel, login_channel
):
    target = account(db_session, "synthetic.receptionist", Role.RECEPTIONIST)
    deactivate(client, channel, target.id)

    with browser() as other:
        response = log_in(other, target.login, login_channel)

        # The same answer as a wrong password, so the status of an account is not revealed.
        assert response.status_code == 401
        if login_channel == "api":
            assert response.json() == {"detail": INVALID_CREDENTIALS}
        else:
            assert INVALID_CREDENTIALS in response.text
        assert other.get("/auth/me", headers=JSON).status_code == 401
    assert sessions_of(db_session, target) == 0


@pytest.mark.parametrize("channel", CHANNELS)
def test_other_accounts_and_the_administrator_keep_their_sessions(
    client, db_session, administrator, channel
):
    target = account(db_session, "synthetic.receptionist", Role.RECEPTIONIST)
    other = account(db_session, "synthetic.receptionist.other", Role.RECEPTIONIST)
    with browser() as other_browser:
        log_in(other_browser, other.login)

        deactivate(client, channel, target.id)

        assert uses_its_session(other_browser, Role.RECEPTIONIST) == (200, 200)
    assert is_active(db_session, other)
    assert uses_its_session(client, Role.ADMINISTRATOR) == (200, 200)


@pytest.mark.parametrize("channel", CHANNELS)
def test_the_account_and_its_doctor_profile_are_kept(client, db_session, administrator, channel):
    target = account(db_session, "synthetic.doctor", Role.DOCTOR)
    profile = Doctor(
        account=target, full_name="Dr Synthetic", specialisation=Specialisation.CARDIOLOGY
    )
    profile.availability = [
        AvailabilityRange(weekday=Weekday.MONDAY, start_time=time(8), end_time=time(12))
    ]
    db_session.add(profile)
    db_session.commit()

    deactivate(client, channel, target.id)

    db_session.expire_all()
    assert db_session.get(StaffAccount, target.id).login == "synthetic.doctor"
    assert (profile.staff_account_id, profile.is_active) == (target.id, True)  # US-16
    assert len(profile.availability) == 1


@pytest.mark.parametrize("channel", CHANNELS)
def test_deactivating_an_inactive_account_changes_nothing(
    client, db_session, administrator, channel
):
    target = account(db_session, "synthetic.receptionist", Role.RECEPTIONIST)
    deactivate(client, channel, target.id)

    response = deactivate(client, channel, target.id)

    assert response.status_code == (200 if channel == "api" else 303)
    assert not is_active(db_session, target)


@pytest.mark.parametrize("channel", CHANNELS)
def test_administrators_cannot_deactivate_their_own_account(
    client, db_session, administrator, channel
):
    response = deactivate(client, channel, administrator.id)

    assert response.status_code == 409
    assert OWN_ACCOUNT in response.text
    assert is_active(db_session, administrator)
    assert uses_its_session(client, Role.ADMINISTRATOR) == (200, 200)


# ---------------------------------------------------------------- criterion 2: access is refused


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR], ids=str)
@pytest.mark.parametrize("target_role", list(Role), ids=str)
def test_receptionists_and_doctors_are_refused(client, db_session, channel, role, target_role):
    target = account(db_session, f"synthetic.{target_role.value}.target", target_role)
    with browser() as target_browser:
        log_in(target_browser, target.login)
        account(db_session, f"synthetic.{role.value}.user", role)
        log_in(client, f"synthetic.{role.value}.user")

        response = deactivate(client, channel, target.id)

        assert response.status_code == 403
        if channel == "api":
            assert response.json() == {"detail": NOT_PERMITTED}
        else:
            assert "Access denied" in response.text
        assert is_active(db_session, target)
        assert uses_its_session(target_browser, target_role) == (200, 200)


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR], ids=str)
def test_receptionists_and_doctors_cannot_open_the_confirmation(client, db_session, role):
    target = account(db_session, "synthetic.target", Role.RECEPTIONIST)
    account(db_session, f"synthetic.{role.value}.user", role)
    log_in(client, f"synthetic.{role.value}.user")

    response = client.get(f"/staff/{target.id}/deactivate", headers=HTML)

    assert response.status_code == 403
    assert "Deactivate account</button>" not in response.text
    assert "synthetic.target" not in response.text


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR], ids=str)
def test_receptionists_and_doctors_cannot_deactivate_themselves(client, db_session, role):
    own = account(db_session, f"synthetic.{role.value}.user", role)
    log_in(client, own.login)

    for channel in CHANNELS:
        assert deactivate(client, channel, own.id).status_code == 403
    assert is_active(db_session, own)


@pytest.mark.parametrize("channel", CHANNELS)
def test_deactivation_without_a_session_is_refused(client, db_session, channel):
    target = account(db_session, "synthetic.receptionist", Role.RECEPTIONIST)

    response = deactivate(client, channel, target.id)

    assert response.status_code == 401
    if channel == "api":
        assert response.json() == {"detail": NOT_AUTHENTICATED}
    else:
        assert "Please log in to continue." in response.text
    assert is_active(db_session, target)


def test_a_deactivated_administrator_can_no_longer_deactivate(client, db_session):
    first = account(db_session, "synthetic.administrator.first", Role.ADMINISTRATOR)
    second = account(db_session, "synthetic.administrator.second", Role.ADMINISTRATOR)
    target = account(db_session, "synthetic.receptionist", Role.RECEPTIONIST)
    log_in(client, first.login)
    with browser() as other_administrator:
        log_in(other_administrator, second.login)
        assert deactivate(other_administrator, "api", first.id).status_code == 200

    response = deactivate(client, "api", target.id)

    assert response.status_code == 401
    assert is_active(db_session, target)
