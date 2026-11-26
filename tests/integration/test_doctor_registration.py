"""Integration tests for doctor registration: the account rules and the API (T-02.2).

Synthetic data only. The acceptance and access tests of US-02 are T-02.4 (#58).
"""

from datetime import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.access import NOT_AUTHENTICATED, NOT_PERMITTED
from app.db import get_session
from app.doctors import MESSAGES, InvalidDoctor, eligible_accounts, validate_doctor
from app.main import app
from app.models import Doctor, Role, Specialisation, StaffAccount, Weekday
from tests.csrf import csrf_headers

PASSWORD = "synthetic-password"
AVAILABILITY = {
    "weekday": ["0", "2"],
    "start_time": ["08:00", "14:00"],
    "end_time": ["12:00", "18:00"],
}


def account(db_session, login: str, role: Role = Role.DOCTOR, active: bool = True):
    staff = StaffAccount(login=login, role=role, is_active=active)
    staff.set_password(PASSWORD)
    db_session.add(staff)
    db_session.commit()
    return staff


def doctor_form(staff_account_id, **fields) -> dict:
    return (
        {
            "staff_account_id": str(staff_account_id),
            "full_name": "Dr Synthetic Doctor",
            "specialisation": "cardiology",
        }
        | AVAILABILITY
        | fields
    )


def validate(db_session, form: dict):
    return validate_doctor(
        db_session,
        form.get("staff_account_id"),
        form.get("full_name"),
        form.get("specialisation"),
        form.get("weekday", []),
        form.get("start_time", []),
        form.get("end_time", []),
    )


def errors_of(db_session, form: dict) -> dict:
    with pytest.raises(InvalidDoctor) as raised:
        validate(db_session, form)
    return raised.value.errors


# ---------------------------------------------------------------- account rules


def test_only_active_doctor_accounts_without_a_profile_are_eligible(db_session):
    free = account(db_session, "synthetic.doctor.free")
    taken = account(db_session, "synthetic.doctor.taken")
    account(db_session, "synthetic.doctor.inactive", active=False)
    account(db_session, "synthetic.receptionist", Role.RECEPTIONIST)
    account(db_session, "synthetic.administrator", Role.ADMINISTRATOR)
    db_session.add(
        Doctor(account=taken, full_name="Dr Taken", specialisation=Specialisation.NEUROLOGY)
    )
    db_session.commit()

    assert eligible_accounts(db_session) == [free]


@pytest.mark.parametrize(
    ("make", "message"),
    [
        (lambda db: "", "account_missing"),
        (lambda db: "abc", "account_unavailable"),
        (lambda db: "999999", "account_unavailable"),
        (
            lambda db: account(db, "synthetic.receptionist", Role.RECEPTIONIST).id,
            "account_unavailable",
        ),
        (
            lambda db: account(db, "synthetic.doctor.inactive", active=False).id,
            "account_unavailable",
        ),
    ],
    ids=["missing", "not-a-number", "unknown", "receptionist", "inactive"],
)
def test_the_account_must_be_an_eligible_doctor_account(db_session, make, message):
    assert errors_of(db_session, doctor_form(make(db_session))) == {
        "staff_account_id": MESSAGES[message]
    }


def test_a_doctor_account_with_a_profile_cannot_get_a_second_one(db_session):
    staff = account(db_session, "synthetic.doctor")
    db_session.add(
        Doctor(account=staff, full_name="Dr First", specialisation=Specialisation.CARDIOLOGY)
    )
    db_session.commit()

    assert errors_of(db_session, doctor_form(staff.id)) == {
        "staff_account_id": MESSAGES["account_unavailable"]
    }


@pytest.mark.parametrize(
    ("fields", "expected"),
    [
        ({"full_name": "  "}, {"full_name": "name_missing"}),
        ({"full_name": "x" * 121}, {"full_name": "name_too_long"}),
        ({"specialisation": ""}, {"specialisation": "specialisation_invalid"}),
        ({"specialisation": "astrology"}, {"specialisation": "specialisation_invalid"}),
    ],
)
def test_name_and_specialisation_rules(db_session, fields, expected):
    staff = account(db_session, "synthetic.doctor")

    assert errors_of(db_session, doctor_form(staff.id, **fields)) == {
        field: MESSAGES[key] for field, key in expected.items()
    }


def test_valid_details_are_cleaned(db_session):
    staff = account(db_session, "synthetic.doctor")

    details = validate(db_session, doctor_form(staff.id, full_name=" Dr Synthetic Doctor "))

    assert (details.staff_account_id, details.full_name, details.specialisation) == (
        staff.id,
        "Dr Synthetic Doctor",
        Specialisation.CARDIOLOGY,
    )
    assert [r.weekday for r in details.availability] == [Weekday.MONDAY, Weekday.WEDNESDAY]


def test_every_invalid_field_is_reported_at_once(db_session):
    form = {
        "staff_account_id": "",
        "full_name": "",
        "specialisation": "",
        "weekday": ["0"],
        "start_time": ["08:15"],
        "end_time": ["12:00"],
    }

    assert errors_of(db_session, form) == {
        "staff_account_id": MESSAGES["account_missing"],
        "full_name": MESSAGES["name_missing"],
        "specialisation": MESSAGES["specialisation_invalid"],
        "availability_1": MESSAGES["range_time"],
    }


# ---------------------------------------------------------------- API


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


def log_in(client, db_session, role: Role) -> None:
    staff = account(db_session, f"synthetic.login.{role.value}", role)
    data = {"login": staff.login, "password": PASSWORD}
    assert client.post("/auth/login", data=data, headers=csrf_headers(client)).status_code == 200


def register(client, form: dict):
    return client.post("/api/doctors", data=form, headers=csrf_headers(client))


def doctor_count(db_session) -> int:
    return db_session.scalar(select(func.count()).select_from(Doctor))


def test_administrators_register_a_doctor_with_availability(client, db_session):
    log_in(client, db_session, Role.ADMINISTRATOR)
    staff = account(db_session, "synthetic.doctor")

    response = register(client, doctor_form(staff.id))

    saved = db_session.scalars(select(Doctor)).one()
    assert response.status_code == 201
    assert response.json() == {
        "id": saved.id,
        "login": "synthetic.doctor",
        "full_name": "Dr Synthetic Doctor",
        "specialisation": "cardiology",
        "is_active": True,
        "availability": [
            {"weekday": 0, "start": "08:00", "end": "12:00"},
            {"weekday": 2, "start": "14:00", "end": "18:00"},
        ],
    }
    assert saved.staff_account_id == staff.id
    assert [(r.weekday, r.start_time) for r in saved.availability] == [
        (Weekday.MONDAY, time(8)),
        (Weekday.WEDNESDAY, time(14)),
    ]


def test_invalid_data_is_rejected_identified_and_saves_nothing(client, db_session):
    log_in(client, db_session, Role.ADMINISTRATOR)
    staff = account(db_session, "synthetic.doctor")

    response = register(
        client, doctor_form(staff.id, specialisation="", end_time=["12:00", "13:00"])
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Invalid doctor data.",
        "errors": {
            "specialisation": MESSAGES["specialisation_invalid"],
            "availability_2": MESSAGES["range_order"],
        },
    }
    assert doctor_count(db_session) == 0


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR])
def test_receptionists_and_doctors_are_refused(client, db_session, role):
    log_in(client, db_session, role)
    staff = account(db_session, "synthetic.doctor")

    response = register(client, doctor_form(staff.id))

    assert (response.status_code, response.json()) == (403, {"detail": NOT_PERMITTED})
    assert doctor_count(db_session) == 0


def test_registration_needs_a_session(client, db_session):
    staff = account(db_session, "synthetic.doctor")

    response = register(client, doctor_form(staff.id))

    assert (response.status_code, response.json()) == (401, {"detail": NOT_AUTHENTICATED})
    assert doctor_count(db_session) == 0
