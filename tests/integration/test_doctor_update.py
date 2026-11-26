"""Integration tests for doctor updates through the API (T-13.1). Synthetic data only.

The acceptance and access tests of US-13, over the API and the pages, are T-13.3 (#64).
"""

from datetime import time

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
CHANGES = {
    "full_name": "Dr Updated Synthetic",
    "specialisation": "neurology",
    "weekday": ["4", "4"],
    "start_time": ["09:00", "13:00"],
    "end_time": ["12:00", "17:30"],
}


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


@pytest.fixture
def doctor(db_session) -> Doctor:
    profile = Doctor(
        account=account(db_session, "synthetic.doctor", Role.DOCTOR),
        full_name="Dr Synthetic",
        specialisation=Specialisation.CARDIOLOGY,
    )
    profile.availability = [
        AvailabilityRange(weekday=Weekday.MONDAY, start_time=time(8), end_time=time(12)),
        AvailabilityRange(weekday=Weekday.WEDNESDAY, start_time=time(14), end_time=time(18)),
    ]
    db_session.add(profile)
    db_session.commit()
    return profile


def log_in(client, login: str) -> None:
    data = {"login": login, "password": PASSWORD}
    assert client.post("/auth/login", data=data, headers=csrf_headers(client)).status_code == 200


def update(client, doctor_id: int, data: dict):
    return client.post(f"/api/doctors/{doctor_id}", data=data, headers=csrf_headers(client))


def stored(db_session, doctor: Doctor) -> tuple:
    db_session.expire_all()
    ranges = [(r.weekday, r.start_time, r.end_time) for r in doctor.availability]
    return (doctor.full_name, doctor.specialisation, ranges)


@pytest.fixture
def administrator(client, db_session):
    account(db_session, "synthetic.administrator", Role.ADMINISTRATOR)
    log_in(client, "synthetic.administrator")


def test_administrators_update_details_and_replace_the_availability(
    client, db_session, administrator, doctor
):
    response = update(client, doctor.id, CHANGES)

    assert response.status_code == 200
    assert response.json() == {
        "id": doctor.id,
        "login": "synthetic.doctor",
        "full_name": "Dr Updated Synthetic",
        "specialisation": "neurology",
        "is_active": True,
        "availability": [
            {"weekday": 4, "start": "09:00", "end": "12:00"},
            {"weekday": 4, "start": "13:00", "end": "17:30"},
        ],
    }
    assert stored(db_session, doctor) == (
        "Dr Updated Synthetic",
        Specialisation.NEUROLOGY,
        [(Weekday.FRIDAY, time(9), time(12)), (Weekday.FRIDAY, time(13), time(17, 30))],
    )
    # The replaced ranges are deleted, and the profile keeps its account and status.
    assert db_session.scalar(select(func.count()).select_from(AvailabilityRange)) == 2
    assert (doctor.staff_account_id, doctor.is_active) == (doctor.account.id, True)


def test_the_account_cannot_be_changed_by_an_update(client, db_session, administrator, doctor):
    other = account(db_session, "synthetic.doctor.other", Role.DOCTOR)

    update(client, doctor.id, CHANGES | {"staff_account_id": str(other.id)})

    db_session.expire_all()
    assert doctor.account.login == "synthetic.doctor"


def test_invalid_changes_are_rejected_identified_and_change_nothing(
    client, db_session, administrator, doctor
):
    before = stored(db_session, doctor)

    response = update(
        client, doctor.id, CHANGES | {"specialisation": "", "start_time": ["09:00", "11:00"]}
    )

    assert response.status_code == 422
    assert response.json()["errors"] == {
        "specialisation": MESSAGES["specialisation_invalid"],
        "availability_2": MESSAGES["range_overlap"],
    }
    assert stored(db_session, doctor) == before


def test_unknown_doctors_are_not_found(client, administrator):
    assert update(client, 999999, CHANGES).status_code == 404


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR])
def test_receptionists_and_doctors_are_refused(client, db_session, doctor, role):
    login = "synthetic.doctor" if role is Role.DOCTOR else "synthetic.receptionist"
    if role is Role.RECEPTIONIST:
        account(db_session, login, role)
    log_in(client, login)  # a doctor cannot update even its own profile
    before = stored(db_session, doctor)

    response = update(client, doctor.id, CHANGES)

    assert (response.status_code, response.json()) == (403, {"detail": NOT_PERMITTED})
    assert stored(db_session, doctor) == before


def test_updates_need_a_session(client, db_session, doctor):
    before = stored(db_session, doctor)

    response = update(client, doctor.id, CHANGES)

    assert (response.status_code, response.json()) == (401, {"detail": NOT_AUTHENTICATED})
    assert stored(db_session, doctor) == before
