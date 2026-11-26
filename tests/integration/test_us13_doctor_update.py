"""Acceptance and access tests of US-13, update doctor details (T-13.3, #64).

Every case runs through both ways of updating a doctor: the JSON API
(`POST /api/doctors/<id>`) and the edit page (`POST /doctors/<id>/edit`). Synthetic data only.

The first criterion also says that existing appointments are retained. Appointments do not
exist yet (US-04, Sprint 3); these tests check that an update keeps the doctor's identity, its
account link and its status and changes no other doctor, which is what appointments will refer to.
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
from app.models import AvailabilityRange, Doctor, Role, Specialisation, StaffAccount, Weekday
from tests.csrf import csrf_headers

PASSWORD = "synthetic-password"
HTML = {"Accept": "text/html"}
JSON = {"Accept": "application/json"}
CHANNELS = ["api", "page"]
BEFORE = (
    "Dr Synthetic",
    Specialisation.CARDIOLOGY,
    [(Weekday.MONDAY, time(8), time(12)), (Weekday.WEDNESDAY, time(14), time(18))],
)


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


def account(db_session, login: str, role: Role = Role.DOCTOR) -> StaffAccount:
    staff = StaffAccount(login=login, role=role)
    staff.set_password(PASSWORD)
    db_session.add(staff)
    db_session.commit()
    return staff


def make_doctor(db_session, login: str, active: bool = True) -> Doctor:
    profile = Doctor(
        account=account(db_session, login),
        full_name="Dr Synthetic",
        specialisation=Specialisation.CARDIOLOGY,
        is_active=active,
    )
    profile.availability = [
        AvailabilityRange(weekday=Weekday.MONDAY, start_time=time(8), end_time=time(12)),
        AvailabilityRange(weekday=Weekday.WEDNESDAY, start_time=time(14), end_time=time(18)),
    ]
    db_session.add(profile)
    db_session.commit()
    return profile


@pytest.fixture
def doctor(db_session) -> Doctor:
    return make_doctor(db_session, "synthetic.doctor")


def log_in(client, db_session, role: Role, login: str | None = None) -> StaffAccount:
    if login is None:
        staff = account(db_session, f"synthetic.login.{role.value}", role)
        login = staff.login
    else:
        staff = db_session.scalar(select(StaffAccount).where(StaffAccount.login == login))
    data = {"login": login, "password": PASSWORD}
    assert client.post("/auth/login", data=data, headers=csrf_headers(client)).status_code == 200
    return staff


def changes(**fields) -> dict:
    """A valid update; ``fields`` replace any value."""
    return {
        "full_name": "Dr Updated Synthetic",
        "specialisation": "dermatology",
        "weekday": ["4", "1"],
        "start_time": ["09:00", "07:30"],
        "end_time": ["13:00", "11:00"],
    } | fields


def update(client, channel: str, doctor_id: int, data: dict):
    """Submit through the API or the page; return the response and the field errors."""
    headers = csrf_headers(client)
    if channel == "api":
        response = client.post(f"/api/doctors/{doctor_id}", data=data, headers=headers | JSON)
        errors = response.json().get("errors", {}) if response.status_code == 422 else {}
        return response, errors
    response = client.post(
        f"/doctors/{doctor_id}/edit", data=data, headers=headers | HTML, follow_redirects=False
    )
    found = re.findall(r'<p class="field-error" id="([\w]+)-error">(.*?)</p>', response.text)
    return response, {key: unescape(message) for key, message in found}


def stored(db_session, doctor: Doctor) -> tuple:
    db_session.expire_all()  # read what the database holds
    ranges = [(r.weekday, r.start_time, r.end_time) for r in doctor.availability]
    return (doctor.full_name, doctor.specialisation, ranges)


def range_count(db_session) -> int:
    return db_session.scalar(select(func.count()).select_from(AvailabilityRange))


# ---------------------------------------------------------------- criterion 1: changes persisted


@pytest.mark.parametrize("channel", CHANNELS)
def test_valid_changes_are_persisted(client, db_session, doctor, channel):
    log_in(client, db_session, Role.ADMINISTRATOR)

    response, errors = update(client, channel, doctor.id, changes())

    assert errors == {}
    assert response.status_code == (200 if channel == "api" else 303)
    assert stored(db_session, doctor) == (
        "Dr Updated Synthetic",
        Specialisation.DERMATOLOGY,
        [(Weekday.TUESDAY, time(7, 30), time(11)), (Weekday.FRIDAY, time(9), time(13))],
    )
    assert range_count(db_session) == 2  # the previous ranges were replaced, not kept


@pytest.mark.parametrize("channel", CHANNELS)
def test_the_changes_are_shown_after_a_reload(client, db_session, doctor, channel):
    log_in(client, db_session, Role.ADMINISTRATOR)
    update(client, channel, doctor.id, changes())

    page = " ".join(
        unescape(
            re.sub(r"<[^>]+>", " ", client.get(f"/doctors/{doctor.id}", headers=HTML).text)
        ).split()
    )

    assert "Dr Updated Synthetic" in page
    assert "Specialisation Dermatology Staff account synthetic.doctor Status Active" in page
    assert "Tuesday 07:30 11:00 Friday 09:00 13:00" in page


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize("active", [True, False], ids=["active", "inactive"])
def test_an_update_keeps_the_doctor_its_account_and_its_status(client, db_session, channel, active):
    doctor = make_doctor(db_session, "synthetic.doctor", active=active)
    other = make_doctor(db_session, "synthetic.doctor.other")
    identity = (doctor.id, doctor.staff_account_id)
    log_in(client, db_session, Role.ADMINISTRATOR)

    update(client, channel, doctor.id, changes(staff_account_id=str(other.staff_account_id)))

    db_session.expire_all()
    assert (doctor.id, doctor.staff_account_id, doctor.is_active) == (*identity, active)
    assert db_session.scalar(select(func.count()).select_from(Doctor)) == 2
    assert stored(db_session, other) == BEFORE  # another doctor is not changed


@pytest.mark.parametrize("channel", CHANNELS)
def test_adjacent_ranges_are_valid(client, db_session, doctor, channel):
    log_in(client, db_session, Role.ADMINISTRATOR)
    data = changes(weekday=["0", "0"], start_time=["08:00", "12:00"], end_time=["12:00", "14:00"])

    _, errors = update(client, channel, doctor.id, data)

    assert errors == {}
    assert len(stored(db_session, doctor)[2]) == 2


# ---------------------------------------------------------------- criterion 2: invalid data


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize(
    ("second", "message"),
    [
        (("1", "07:30", ""), "range_incomplete"),
        (("7", "07:30", "11:00"), "range_weekday"),
        (("1", "07:45", "11:00"), "range_time"),
        (("1", "11:00", "07:30"), "range_order"),
        (("4", "12:30", "15:00"), "range_overlap"),
    ],
    ids=["incomplete", "weekday", "off-grid", "end-before-start", "overlap"],
)
def test_invalid_availability_is_rejected_and_its_row_identified(
    client, db_session, doctor, channel, second, message
):
    log_in(client, db_session, Role.ADMINISTRATOR)
    day, start, end = second
    data = changes(weekday=["4", day], start_time=["09:00", start], end_time=["13:00", end])

    response, errors = update(client, channel, doctor.id, data)

    assert response.status_code == 422
    assert errors == {"availability_2": MESSAGES[message]}
    assert stored(db_session, doctor) == BEFORE


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        ({"full_name": "  "}, {"full_name": "name_missing"}),
        ({"full_name": "D" * 121}, {"full_name": "name_too_long"}),
        ({"specialisation": "astrology"}, {"specialisation": "specialisation_invalid"}),
        (
            {"weekday": [""], "start_time": [""], "end_time": [""]},
            {"availability": "availability_missing"},
        ),
    ],
    ids=["no-name", "long-name", "specialisation", "no-range"],
)
def test_missing_or_invalid_details_are_rejected_and_identified(
    client, db_session, doctor, channel, fields, expected
):
    log_in(client, db_session, Role.ADMINISTRATOR)

    response, errors = update(client, channel, doctor.id, changes(**fields))

    assert response.status_code == 422
    assert errors == {key: MESSAGES[message] for key, message in expected.items()}
    assert stored(db_session, doctor) == BEFORE


@pytest.mark.parametrize("channel", CHANNELS)
def test_every_invalid_field_is_identified_at_once(client, db_session, doctor, channel):
    log_in(client, db_session, Role.ADMINISTRATOR)
    data = changes(full_name="", specialisation="", start_time=["09:00", "07:45"])

    response, errors = update(client, channel, doctor.id, data)

    assert response.status_code == 422
    assert errors == {
        "full_name": MESSAGES["name_missing"],
        "specialisation": MESSAGES["specialisation_invalid"],
        "availability_2": MESSAGES["range_time"],
    }
    assert stored(db_session, doctor) == BEFORE


# ---------------------------------------------------------------- criterion 3: access is refused


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR])
def test_receptionists_and_doctors_are_refused(client, db_session, doctor, channel, role):
    log_in(client, db_session, role)

    response, _ = update(client, channel, doctor.id, changes())

    assert response.status_code == 403
    if channel == "api":
        assert response.json() == {"detail": NOT_PERMITTED}
    else:
        assert "Access denied" in response.text
    assert stored(db_session, doctor) == BEFORE


@pytest.mark.parametrize("channel", CHANNELS)
def test_a_doctor_cannot_update_its_own_profile(client, db_session, doctor, channel):
    log_in(client, db_session, Role.DOCTOR, login="synthetic.doctor")

    response, _ = update(client, channel, doctor.id, changes())

    assert response.status_code == 403
    assert stored(db_session, doctor) == BEFORE


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR])
def test_receptionists_and_doctors_cannot_open_the_edit_form(client, db_session, doctor, role):
    log_in(client, db_session, role)

    response = client.get(f"/doctors/{doctor.id}/edit", headers=HTML)

    assert response.status_code == 403
    assert "Dr Synthetic" not in response.text
    assert 'name="full_name"' not in response.text


@pytest.mark.parametrize("channel", CHANNELS)
def test_updates_without_a_session_are_refused(client, db_session, doctor, channel):
    response, _ = update(client, channel, doctor.id, changes())

    assert response.status_code == 401
    if channel == "api":
        assert response.json() == {"detail": NOT_AUTHENTICATED}
    else:
        assert "Please log in to continue." in response.text
    assert stored(db_session, doctor) == BEFORE


def test_a_deactivated_administrator_can_no_longer_update(client, db_session, doctor):
    administrator = log_in(client, db_session, Role.ADMINISTRATOR)
    administrator.is_active = False
    db_session.commit()

    response, _ = update(client, "api", doctor.id, changes())

    assert response.status_code == 401
    assert stored(db_session, doctor) == BEFORE


@pytest.mark.parametrize("channel", CHANNELS)
def test_an_unknown_doctor_is_not_found(client, db_session, doctor, channel):
    log_in(client, db_session, Role.ADMINISTRATOR)

    response, _ = update(client, channel, doctor.id + 1000, changes())

    assert response.status_code == 404
    assert stored(db_session, doctor) == BEFORE
