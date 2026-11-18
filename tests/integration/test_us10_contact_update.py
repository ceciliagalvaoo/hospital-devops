"""Acceptance and access tests of US-10, edit patient contact details (T-10.3, #45).

Every case runs through both ways of updating contacts: the JSON API
(`POST /api/patients/<id>/contacts`) and the contact-edit page (`POST /patients/<id>/contacts`).
Synthetic data only.
"""

import re
from datetime import date
from html import unescape

import pytest
from fastapi.testclient import TestClient

from app.access import NOT_AUTHENTICATED, NOT_PERMITTED
from app.db import get_session
from app.main import app
from app.models import Patient, Role, StaffAccount
from app.patients import MESSAGES
from tests.csrf import csrf_headers

PASSWORD = "synthetic-password"
HTML = {"Accept": "text/html"}
JSON = {"Accept": "application/json"}
CHANNELS = ["api", "page"]
OLD = ("+55 11 90000-0000", "old.address@example.test")
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
        full_name="Synthetic Patient", date_of_birth=date(1990, 5, 17), phone=OLD[0], email=OLD[1]
    )
    db_session.add(saved)
    db_session.commit()
    return saved


def log_in(client, db_session, role: Role) -> StaffAccount:
    account = StaffAccount(login=f"synthetic.{role.value}", role=role)
    account.set_password(PASSWORD)
    db_session.add(account)
    db_session.commit()
    data = {"login": account.login, "password": PASSWORD}
    assert client.post("/auth/login", data=data, headers=csrf_headers(client)).status_code == 200
    return account


def update(client, channel: str, patient_id: int, data: dict):
    """Submit through the API or the page; return the response and the field errors."""
    headers = csrf_headers(client)
    if channel == "api":
        response = client.post(
            f"/api/patients/{patient_id}/contacts", data=data, headers=headers | JSON
        )
        errors = response.json().get("errors", {}) if response.status_code == 422 else {}
        return response, errors
    response = client.post(
        f"/patients/{patient_id}/contacts",
        data=data,
        headers=headers | HTML,
        follow_redirects=False,
    )
    found = re.findall(r'<p class="field-error" id="(\w+)-error">(.*?)</p>', response.text)
    return response, {field: unescape(message) for field, message in found}


def stored(db_session, patient: Patient) -> tuple:
    db_session.expire_all()  # read what the database holds, not the object in memory
    return (patient.full_name, patient.date_of_birth, patient.phone, patient.email)


def record_text(client, patient: Patient) -> str:
    page = client.get(f"/patients/{patient.id}", headers=HTML).text
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", page)).split())


# ---------------------------------------------------------------- criterion 1: saved and shown


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.ADMINISTRATOR])
def test_valid_contacts_are_saved_and_shown_after_reloading_the_record(
    client, db_session, patient, role, channel
):
    log_in(client, db_session, role)

    response, errors = update(client, channel, patient.id, NEW)

    assert errors == {}
    assert response.status_code == (200 if channel == "api" else 303)
    assert stored(db_session, patient) == (
        "Synthetic Patient",
        date(1990, 5, 17),
        NEW["phone"],
        NEW["email"],
    )
    assert f"Phone {NEW['phone']} E-mail {NEW['email']}" in record_text(client, patient)


@pytest.mark.parametrize("channel", CHANNELS)
def test_one_contact_can_change_and_an_empty_one_is_removed(client, db_session, patient, channel):
    log_in(client, db_session, Role.RECEPTIONIST)

    update(client, channel, patient.id, {"phone": OLD[0], "email": ""})

    assert stored(db_session, patient)[2:] == (OLD[0], None)
    assert f"Phone {OLD[0]} E-mail Not given" in record_text(client, patient)


@pytest.mark.parametrize("channel", CHANNELS)
def test_values_are_trimmed(client, db_session, patient, channel):
    log_in(client, db_session, Role.RECEPTIONIST)

    update(
        client, channel, patient.id, {"phone": f"  {NEW['phone']} ", "email": f" {NEW['email']}"}
    )

    assert stored(db_session, patient)[2:] == (NEW["phone"], NEW["email"])


# ---------------------------------------------------------------- criterion 2: invalid details


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize(
    ("data", "expected"),
    [
        ({"phone": "12", "email": NEW["email"]}, {"phone": "phone_invalid"}),
        ({"phone": "1" * 16, "email": NEW["email"]}, {"phone": "phone_invalid"}),
        ({"phone": "11 9123 abcd", "email": NEW["email"]}, {"phone": "phone_invalid"}),
        ({"phone": NEW["phone"], "email": "patient@"}, {"email": "email_invalid"}),
        ({"phone": NEW["phone"], "email": "pa tient@example.test"}, {"email": "email_invalid"}),
        ({"phone": "12", "email": "nope"}, {"phone": "phone_invalid", "email": "email_invalid"}),
    ],
    ids=["short-phone", "long-phone", "letters", "no-domain", "space", "both"],
)
def test_invalid_contacts_are_rejected_identified_and_change_nothing(
    client, db_session, patient, channel, data, expected
):
    log_in(client, db_session, Role.RECEPTIONIST)

    response, errors = update(client, channel, patient.id, data)

    assert response.status_code == 422
    assert errors == {field: MESSAGES[key] for field, key in expected.items()}
    assert stored(db_session, patient)[2:] == OLD
    assert f"Phone {OLD[0]} E-mail {OLD[1]}" in record_text(client, patient)


# ---------------------------------------------------------------- criterion 3: access is refused


def test_doctors_are_refused_by_the_api(client, db_session, patient):
    log_in(client, db_session, Role.DOCTOR)

    response, _ = update(client, "api", patient.id, NEW)

    assert (response.status_code, response.json()) == (403, {"detail": NOT_PERMITTED})
    assert stored(db_session, patient)[2:] == OLD


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_doctors_are_refused_by_the_contact_form(client, db_session, patient, method):
    log_in(client, db_session, Role.DOCTOR)

    response = client.request(
        method,
        f"/patients/{patient.id}/contacts",
        data=NEW,
        headers=csrf_headers(client) | HTML,
        follow_redirects=False,
    )

    assert response.status_code == 403
    assert "Access denied" in response.text
    assert OLD[1] not in response.text  # the current contacts are not shown
    assert stored(db_session, patient)[2:] == OLD


@pytest.mark.parametrize("channel", CHANNELS)
def test_updates_without_a_session_are_refused(client, db_session, patient, channel):
    response, _ = update(client, channel, patient.id, NEW)

    assert response.status_code == 401
    if channel == "api":
        assert response.json() == {"detail": NOT_AUTHENTICATED}
    else:
        assert "Please log in to continue." in response.text
    assert stored(db_session, patient)[2:] == OLD


def test_a_deactivated_account_can_no_longer_update(client, db_session, patient):
    account = log_in(client, db_session, Role.RECEPTIONIST)
    account.is_active = False
    db_session.commit()

    response, _ = update(client, "api", patient.id, NEW)

    assert response.status_code == 401
    assert stored(db_session, patient)[2:] == OLD


@pytest.mark.parametrize("channel", CHANNELS)
def test_unknown_patients_are_not_found(client, db_session, channel):
    log_in(client, db_session, Role.RECEPTIONIST)

    response, _ = update(client, channel, 999999, NEW)

    assert response.status_code == 404
