"""Integration tests for patient registration through the API (T-03.2). Synthetic data only.

The full acceptance and access tests of US-03, over the API and the pages, are T-03.4 (#34).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.access import NOT_AUTHENTICATED, NOT_PERMITTED
from app.db import get_session
from app.main import app
from app.models import Patient, Role, StaffAccount
from app.patients import MESSAGES
from tests.csrf import csrf_headers

PASSWORD = "synthetic-password"
PATIENT = {
    "full_name": "Synthetic Patient",
    "date_of_birth": "1990-05-17",
    "phone": "+55 11 90000-0000",
    "email": "patient@example.test",
}


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


def log_in(client, db_session, role: Role) -> None:
    account = StaffAccount(login=f"synthetic.{role.value}", role=role)
    account.set_password(PASSWORD)
    db_session.add(account)
    db_session.commit()
    response = client.post(
        "/auth/login",
        data={"login": account.login, "password": PASSWORD},
        headers=csrf_headers(client),
    )
    assert response.status_code == 200


def register(client, data=PATIENT):
    return client.post("/api/patients", data=data, headers=csrf_headers(client))


def patient_count(db_session) -> int:
    return db_session.scalar(select(func.count()).select_from(Patient))


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.ADMINISTRATOR])
def test_front_desk_roles_register_a_patient(client, db_session, role):
    log_in(client, db_session, role)

    response = register(client)

    saved = db_session.scalars(select(Patient)).one()
    assert response.status_code == 201
    assert response.json() == PATIENT | {"record_number": saved.record_number, "is_active": True}
    assert (saved.full_name, saved.email) == ("Synthetic Patient", "patient@example.test")


def test_missing_required_fields_are_rejected_and_identified(client, db_session):
    log_in(client, db_session, Role.RECEPTIONIST)

    response = register(client, {"phone": "", "email": ""})

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Invalid patient data.",
        "errors": {
            "full_name": MESSAGES["name_missing"],
            "date_of_birth": MESSAGES["birth_missing"],
        },
    }
    assert patient_count(db_session) == 0


def test_doctors_are_refused(client, db_session):
    log_in(client, db_session, Role.DOCTOR)

    response = register(client)

    assert (response.status_code, response.json()) == (403, {"detail": NOT_PERMITTED})
    assert patient_count(db_session) == 0


def test_unauthenticated_requests_are_refused(client, db_session):
    response = register(client)

    assert (response.status_code, response.json()) == (401, {"detail": NOT_AUTHENTICATED})
    assert patient_count(db_session) == 0
