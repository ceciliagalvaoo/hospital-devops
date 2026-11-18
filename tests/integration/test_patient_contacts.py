"""Integration tests for patient contact updates through the API (T-10.1). Synthetic data only.

The acceptance and access tests of US-10, over the API and the pages, are T-10.3 (#45).
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.access import NOT_AUTHENTICATED, NOT_PERMITTED
from app.db import get_session
from app.main import app
from app.models import Patient, Role, StaffAccount
from app.patients import MESSAGES
from tests.csrf import csrf_headers

PASSWORD = "synthetic-password"
NEW = {"phone": "+55 21 98888-7777", "email": "new.address@example.test"}


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def patient(db_session) -> Patient:
    saved = Patient(
        full_name="Synthetic Patient",
        date_of_birth=date(1990, 5, 17),
        phone="+55 11 90000-0000",
        email="old.address@example.test",
    )
    db_session.add(saved)
    db_session.commit()
    return saved


def log_in(client, db_session, role: Role) -> None:
    account = StaffAccount(login=f"synthetic.{role.value}", role=role)
    account.set_password(PASSWORD)
    db_session.add(account)
    db_session.commit()
    data = {"login": account.login, "password": PASSWORD}
    assert client.post("/auth/login", data=data, headers=csrf_headers(client)).status_code == 200


def update(client, patient_id: int, data: dict):
    return client.post(
        f"/api/patients/{patient_id}/contacts", data=data, headers=csrf_headers(client)
    )


def stored(db_session, patient: Patient) -> tuple:
    db_session.expire_all()  # read what the database holds
    return (patient.full_name, patient.date_of_birth, patient.phone, patient.email)


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.ADMINISTRATOR])
def test_front_desk_roles_update_the_contacts(client, db_session, patient, role):
    log_in(client, db_session, role)

    response = update(client, patient.id, NEW)

    assert response.status_code == 200
    assert (
        response.json()
        == {
            "record_number": patient.record_number,
            "full_name": "Synthetic Patient",
            "date_of_birth": "1990-05-17",
            "is_active": True,
        }
        | NEW
    )
    assert stored(db_session, patient) == (
        "Synthetic Patient",
        date(1990, 5, 17),
        NEW["phone"],
        NEW["email"],
    )


def test_a_blank_field_removes_that_contact(client, db_session, patient):
    log_in(client, db_session, Role.RECEPTIONIST)

    response = update(client, patient.id, {"phone": "", "email": NEW["email"]})

    assert response.json()["phone"] is None
    assert stored(db_session, patient)[2:] == (None, NEW["email"])


def test_invalid_contacts_are_rejected_identified_and_change_nothing(client, db_session, patient):
    log_in(client, db_session, Role.RECEPTIONIST)

    response = update(client, patient.id, {"phone": "12", "email": "nope"})

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Invalid patient data.",
        "errors": {"phone": MESSAGES["phone_invalid"], "email": MESSAGES["email_invalid"]},
    }
    assert stored(db_session, patient)[2:] == ("+55 11 90000-0000", "old.address@example.test")


def test_unknown_patients_are_not_found(client, db_session):
    log_in(client, db_session, Role.RECEPTIONIST)

    assert update(client, 999999, NEW).status_code == 404


def test_doctors_are_refused_and_nothing_changes(client, db_session, patient):
    log_in(client, db_session, Role.DOCTOR)

    response = update(client, patient.id, NEW)

    assert (response.status_code, response.json()) == (403, {"detail": NOT_PERMITTED})
    assert stored(db_session, patient)[2:] == ("+55 11 90000-0000", "old.address@example.test")


def test_updates_need_a_session(client, db_session, patient):
    response = update(client, patient.id, NEW)

    assert (response.status_code, response.json()) == (401, {"detail": NOT_AUTHENTICATED})
    assert stored(db_session, patient)[2:] == ("+55 11 90000-0000", "old.address@example.test")
