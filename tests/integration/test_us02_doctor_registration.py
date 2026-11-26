"""Acceptance and access tests of US-02, register a doctor (T-02.4, #58).

Every case runs through both ways of registering a doctor: the JSON API (`POST /api/doctors`)
and the registration page (`POST /doctors/new`). Synthetic data only.
"""

import re
from datetime import time
from html import unescape

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.access import NOT_AUTHENTICATED, NOT_PERMITTED
from app.db import get_session
from app.doctors import MESSAGES
from app.main import app
from app.models import Doctor, Role, Specialisation, StaffAccount, Weekday
from tests.csrf import csrf_headers

PASSWORD = "synthetic-password"
HTML = {"Accept": "text/html"}
JSON = {"Accept": "application/json"}
CHANNELS = ["api", "page"]


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


def account(db_session, login: str, role: Role = Role.DOCTOR, active: bool = True):
    staff = StaffAccount(login=login, role=role, is_active=active)
    staff.set_password(PASSWORD)
    db_session.add(staff)
    db_session.commit()
    return staff


@pytest.fixture
def doctor_account(db_session) -> StaffAccount:
    return account(db_session, "synthetic.doctor")


def log_in(client, db_session, role: Role) -> StaffAccount:
    staff = account(db_session, f"synthetic.login.{role.value}", role)
    data = {"login": staff.login, "password": PASSWORD}
    assert client.post("/auth/login", data=data, headers=csrf_headers(client)).status_code == 200
    return staff


def form(staff_id, /, **fields) -> dict:
    """A valid registration for the account ``staff_id``; ``fields`` replace any value."""
    return {
        "staff_account_id": str(staff_id),
        "full_name": "Dr Synthetic Doctor",
        "specialisation": "paediatrics",
        "weekday": ["0", "3"],
        "start_time": ["08:00", "13:30"],
        "end_time": ["12:00", "17:00"],
    } | fields


def register(client, channel: str, data: dict):
    """Submit through the API or the page; return the response and the field errors."""
    headers = csrf_headers(client)
    if channel == "api":
        response = client.post("/api/doctors", data=data, headers=headers | JSON)
        errors = response.json().get("errors", {}) if response.status_code == 422 else {}
        return response, errors
    response = client.post(
        "/doctors/new", data=data, headers=headers | HTML, follow_redirects=False
    )
    found = re.findall(r'<p class="field-error" id="([\w]+)-error">(.*?)</p>', response.text)
    return response, {key: unescape(message) for key, message in found}


def stored_doctors(db_session) -> list[Doctor]:
    db_session.expire_all()  # read what the database holds
    return list(db_session.scalars(select(Doctor)))


def doctor_count(db_session) -> int:
    return db_session.scalar(select(func.count()).select_from(Doctor))


# ---------------------------------------------------------------- criterion 1: saved and linked


@pytest.mark.parametrize("channel", CHANNELS)
def test_a_valid_doctor_is_saved_active_and_linked_to_the_doctor_account(
    client, db_session, doctor_account, channel
):
    log_in(client, db_session, Role.ADMINISTRATOR)

    response, errors = register(client, channel, form(doctor_account.id))

    assert errors == {}
    assert response.status_code == (201 if channel == "api" else 303)
    [doctor] = stored_doctors(db_session)
    assert (doctor.full_name, doctor.specialisation, doctor.is_active) == (
        "Dr Synthetic Doctor",
        Specialisation.PAEDIATRICS,
        True,
    )
    assert doctor.staff_account_id == doctor_account.id
    assert doctor.account.role is Role.DOCTOR
    assert [(r.weekday, r.start_time, r.end_time) for r in doctor.availability] == [
        (Weekday.MONDAY, time(8), time(12)),
        (Weekday.THURSDAY, time(13, 30), time(17)),
    ]


@pytest.mark.parametrize("channel", CHANNELS)
def test_the_saved_doctor_is_shown_on_its_profile_and_in_the_doctors_area(
    client, db_session, doctor_account, channel
):
    log_in(client, db_session, Role.ADMINISTRATOR)
    register(client, channel, form(doctor_account.id))
    [doctor] = stored_doctors(db_session)

    profile = client.get(f"/doctors/{doctor.id}", headers=HTML).text
    area = client.get("/doctors", headers=HTML).text

    text = " ".join(unescape(re.sub(r"<[^>]+>", " ", profile)).split())
    assert "Specialisation Paediatrics Staff account synthetic.doctor Status Active" in text
    assert "Monday 08:00 12:00 Thursday 13:30 17:00" in text
    assert f'<a href="/doctors/{doctor.id}">Dr Synthetic Doctor</a>' in area


# ---------------------------------------------------------------- account association


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize(
    "make",
    [
        lambda db: account(db, "synthetic.receptionist", Role.RECEPTIONIST),
        lambda db: account(db, "synthetic.administrator", Role.ADMINISTRATOR),
        lambda db: account(db, "synthetic.doctor.inactive", active=False),
    ],
    ids=["receptionist-account", "administrator-account", "inactive-doctor-account"],
)
def test_only_an_active_doctor_account_can_be_linked(client, db_session, channel, make):
    log_in(client, db_session, Role.ADMINISTRATOR)
    staff = make(db_session)

    response, errors = register(client, channel, form(staff.id))

    assert response.status_code == 422
    assert errors == {"staff_account_id": MESSAGES["account_unavailable"]}
    assert doctor_count(db_session) == 0


@pytest.mark.parametrize("channel", CHANNELS)
def test_an_account_is_linked_to_one_doctor_only(client, db_session, doctor_account, channel):
    log_in(client, db_session, Role.ADMINISTRATOR)
    register(client, "api", form(doctor_account.id))

    response, errors = register(client, channel, form(doctor_account.id, full_name="Dr Second"))

    assert response.status_code == 422
    assert errors == {"staff_account_id": MESSAGES["account_unavailable"]}
    assert [d.full_name for d in stored_doctors(db_session)] == ["Dr Synthetic Doctor"]


# ---------------------------------------------------------------- criterion 2: invalid data


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        ({"staff_account_id": ""}, {"staff_account_id": "account_missing"}),
        ({"full_name": " "}, {"full_name": "name_missing"}),
        ({"specialisation": ""}, {"specialisation": "specialisation_invalid"}),
        (
            {"weekday": [], "start_time": [], "end_time": []},
            {"availability": "availability_missing"},
        ),
    ],
    ids=["account", "name", "specialisation", "availability"],
)
def test_missing_required_details_are_rejected_and_identified(
    client, db_session, doctor_account, channel, fields, expected
):
    log_in(client, db_session, Role.ADMINISTRATOR)

    response, errors = register(client, channel, form(doctor_account.id, **fields))

    assert response.status_code == 422
    assert errors == {field: MESSAGES[key] for field, key in expected.items()}
    assert doctor_count(db_session) == 0


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize(
    ("second", "message"),
    [
        (("3", "13:30", ""), "range_incomplete"),
        (("8", "13:30", "17:00"), "range_weekday"),
        (("3", "13:15", "17:00"), "range_time"),
        (("3", "17:00", "13:30"), "range_order"),
        (("0", "11:30", "13:00"), "range_overlap"),
    ],
    ids=["incomplete", "weekday", "off-grid", "end-before-start", "overlap"],
)
def test_invalid_availability_is_rejected_and_its_row_identified(
    client, db_session, doctor_account, channel, second, message
):
    log_in(client, db_session, Role.ADMINISTRATOR)
    day, start, end = second
    data = form(
        doctor_account.id, weekday=["0", day], start_time=["08:00", start], end_time=["12:00", end]
    )

    response, errors = register(client, channel, data)

    assert response.status_code == 422
    assert errors == {"availability_2": MESSAGES[message]}
    assert doctor_count(db_session) == 0


@pytest.mark.parametrize("channel", CHANNELS)
def test_adjacent_ranges_are_valid(client, db_session, doctor_account, channel):
    log_in(client, db_session, Role.ADMINISTRATOR)
    data = form(
        doctor_account.id,
        weekday=["0", "0"],
        start_time=["08:00", "12:00"],
        end_time=["12:00", "14:00"],
    )

    _, errors = register(client, channel, data)

    assert errors == {}
    assert len(stored_doctors(db_session)[0].availability) == 2


# ---------------------------------------------------------------- criterion 3: access is refused


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR])
def test_receptionists_and_doctors_are_refused(client, db_session, doctor_account, channel, role):
    log_in(client, db_session, role)

    response, _ = register(client, channel, form(doctor_account.id))

    assert response.status_code == 403
    if channel == "api":
        assert response.json() == {"detail": NOT_PERMITTED}
    else:
        assert "Access denied" in response.text
    assert doctor_count(db_session) == 0


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR])
def test_receptionists_and_doctors_cannot_open_the_form(client, db_session, role):
    log_in(client, db_session, role)

    response = client.get("/doctors/new", headers=HTML)

    assert response.status_code == 403
    assert "staff_account_id" not in response.text


@pytest.mark.parametrize("channel", CHANNELS)
def test_registration_without_a_session_is_refused(client, db_session, doctor_account, channel):
    response, _ = register(client, channel, form(doctor_account.id))

    assert response.status_code == 401
    if channel == "api":
        assert response.json() == {"detail": NOT_AUTHENTICATED}
    else:
        assert "Please log in to continue." in response.text
    assert doctor_count(db_session) == 0


def test_a_deactivated_administrator_can_no_longer_register(client, db_session, doctor_account):
    administrator = log_in(client, db_session, Role.ADMINISTRATOR)
    administrator.is_active = False
    db_session.commit()

    response, _ = register(client, "api", form(doctor_account.id))

    assert response.status_code == 401
    assert doctor_count(db_session) == 0
