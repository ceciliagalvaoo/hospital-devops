"""Acceptance and access tests of US-03, register a patient (T-03.4, #34).

Every case runs through both ways of registering a patient: the JSON API (`POST /api/patients`)
and the registration page (`POST /patients/new`). Synthetic data only.
"""

import re
from datetime import date, timedelta
from html import unescape

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
HTML = {"Accept": "text/html"}
JSON = {"Accept": "application/json"}
PATIENT = {
    "full_name": "Synthetic Patient",
    "date_of_birth": "1990-05-17",
    "phone": "+55 11 90000-0000",
    "email": "patient@example.test",
}
CHANNELS = ["api", "page"]


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


def log_in(client, db_session, role: Role) -> StaffAccount:
    account = StaffAccount(login=f"synthetic.{role.value}", role=role)
    account.set_password(PASSWORD)
    db_session.add(account)
    db_session.commit()
    data = {"login": account.login, "password": PASSWORD}
    assert client.post("/auth/login", data=data, headers=csrf_headers(client)).status_code == 200
    return account


def register(client, channel: str, data: dict):
    """Submit the data through the API or the page; return the response and the field errors."""
    headers = csrf_headers(client)
    if channel == "api":
        response = client.post("/api/patients", data=data, headers=headers | JSON)
        errors = response.json().get("errors", {}) if response.status_code == 422 else {}
        return response, errors
    response = client.post(
        "/patients/new", data=data, headers=headers | HTML, follow_redirects=False
    )
    found = re.findall(r'<p class="field-error" id="(\w+)-error">(.*?)</p>', response.text)
    return response, {field: unescape(message) for field, message in found}


def stored_patients(db_session) -> list[Patient]:
    db_session.expire_all()  # read what the database holds, not the objects in memory
    return list(db_session.scalars(select(Patient)))


def patient_count(db_session) -> int:
    return db_session.scalar(select(func.count()).select_from(Patient))


# ---------------------------------------------------------------- criterion 1: valid data is saved


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.ADMINISTRATOR])
def test_valid_patient_is_saved_with_every_field(client, db_session, role, channel):
    log_in(client, db_session, role)

    response, errors = register(client, channel, PATIENT)

    assert errors == {}
    assert response.status_code == (201 if channel == "api" else 303)
    [patient] = stored_patients(db_session)
    assert (patient.full_name, patient.date_of_birth, patient.phone, patient.email) == (
        "Synthetic Patient",
        date(1990, 5, 17),
        "+55 11 90000-0000",
        "patient@example.test",
    )
    assert patient.is_active is True
    assert patient.created_at is not None


@pytest.mark.parametrize("channel", CHANNELS)
def test_saved_patient_is_shown_on_its_record(client, db_session, channel):
    log_in(client, db_session, Role.RECEPTIONIST)
    register(client, channel, PATIENT)
    [patient] = stored_patients(db_session)

    page = client.get(f"/patients/{patient.id}", headers=HTML)

    assert page.status_code == 200
    assert patient.record_number in page.text
    assert "Synthetic Patient" in page.text


@pytest.mark.parametrize("channel", CHANNELS)
def test_only_name_and_date_of_birth_are_needed(client, db_session, channel):
    log_in(client, db_session, Role.RECEPTIONIST)

    response, errors = register(
        client, channel, {"full_name": "  Synthetic Patient ", "date_of_birth": "1990-05-17"}
    )

    assert errors == {}
    [patient] = stored_patients(db_session)
    assert (patient.full_name, patient.phone, patient.email) == ("Synthetic Patient", None, None)


def test_each_registration_gets_its_own_record_number(client, db_session):
    log_in(client, db_session, Role.RECEPTIONIST)

    numbers = {register(client, "api", PATIENT)[0].json()["record_number"] for _ in range(3)}

    assert len(numbers) == 3
    assert patient_count(db_session) == 3


# ---------------------------------------------------------------- criterion 2: missing fields


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize(
    ("missing", "expected"),
    [
        ({"full_name": ""}, {"full_name": MESSAGES["name_missing"]}),
        ({"full_name": "   "}, {"full_name": MESSAGES["name_missing"]}),
        ({"date_of_birth": ""}, {"date_of_birth": MESSAGES["birth_missing"]}),
        (
            {"full_name": "", "date_of_birth": ""},
            {"full_name": MESSAGES["name_missing"], "date_of_birth": MESSAGES["birth_missing"]},
        ),
    ],
    ids=["name", "blank-name", "date-of-birth", "both"],
)
def test_missing_required_fields_are_rejected_and_identified(
    client, db_session, channel, missing, expected
):
    log_in(client, db_session, Role.RECEPTIONIST)

    response, errors = register(client, channel, PATIENT | missing)

    assert response.status_code == 422
    assert errors == expected
    assert patient_count(db_session) == 0


# ---------------------------------------------------------------- invalid dates (T-03.4)


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize(
    ("value", "message"),
    [
        ("1990-02-30", "birth_invalid"),
        ("1990-13-01", "birth_invalid"),
        ("17/05/1990", "birth_invalid"),
        ("tomorrow", "birth_future"),
        ("1899-12-31", "birth_too_early"),
    ],
)
def test_invalid_dates_of_birth_are_rejected(client, db_session, channel, value, message):
    log_in(client, db_session, Role.RECEPTIONIST)
    if value == "tomorrow":
        value = (date.today() + timedelta(days=1)).isoformat()

    response, errors = register(client, channel, PATIENT | {"date_of_birth": value})

    assert response.status_code == 422
    assert errors == {"date_of_birth": MESSAGES[message]}
    assert patient_count(db_session) == 0


@pytest.mark.parametrize("channel", CHANNELS)
def test_a_patient_born_today_is_accepted(client, db_session, channel):
    log_in(client, db_session, Role.RECEPTIONIST)

    _, errors = register(client, channel, PATIENT | {"date_of_birth": date.today().isoformat()})

    assert errors == {}
    assert stored_patients(db_session)[0].date_of_birth == date.today()


# ---------------------------------------------------------------- criterion 3: access is refused


def test_doctors_are_refused_by_the_api(client, db_session):
    log_in(client, db_session, Role.DOCTOR)

    response, _ = register(client, "api", PATIENT)

    assert (response.status_code, response.json()) == (403, {"detail": NOT_PERMITTED})
    assert patient_count(db_session) == 0


@pytest.mark.parametrize(("method", "path"), [("GET", "/patients/new"), ("POST", "/patients/new")])
def test_doctors_are_refused_by_the_registration_page(client, db_session, method, path):
    log_in(client, db_session, Role.DOCTOR)

    response = client.request(
        method, path, data=PATIENT, headers=csrf_headers(client) | HTML, follow_redirects=False
    )

    assert response.status_code == 403
    assert "Access denied" in response.text
    assert patient_count(db_session) == 0


def test_doctors_cannot_open_a_patient_record_through_the_registration_pages(client, db_session):
    log_in(client, db_session, Role.RECEPTIONIST)
    register(client, "api", PATIENT)
    [patient] = stored_patients(db_session)
    client.cookies.clear()
    log_in(client, db_session, Role.DOCTOR)

    response = client.get(f"/patients/{patient.id}", headers=HTML)

    assert response.status_code == 403
    assert "Synthetic Patient" not in response.text


@pytest.mark.parametrize("channel", CHANNELS)
def test_requests_without_a_session_are_refused(client, db_session, channel):
    response, _ = register(client, channel, PATIENT)

    assert response.status_code == 401
    if channel == "api":
        assert response.json() == {"detail": NOT_AUTHENTICATED}
    else:
        assert "Please log in to continue." in response.text
    assert patient_count(db_session) == 0


def test_a_deactivated_account_can_no_longer_register(client, db_session):
    account = log_in(client, db_session, Role.RECEPTIONIST)
    account.is_active = False
    db_session.commit()

    response, _ = register(client, "api", PATIENT)

    assert response.status_code == 401
    assert patient_count(db_session) == 0
