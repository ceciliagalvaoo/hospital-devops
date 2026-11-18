"""Integration tests for the patient registration page and record page (T-03.3).

Synthetic data only. The acceptance and access tests of US-03 over the API and the pages
are T-03.4 (#34).
"""

import re
from html import unescape

import pytest
from fastapi.testclient import TestClient
from markupsafe import escape
from sqlalchemy import func, select

from app.db import get_session
from app.main import app
from app.models import Patient, Role, StaffAccount
from app.patients import MESSAGES

PASSWORD = "synthetic-password"
HTML = {"Accept": "text/html"}
PATIENT = {
    "full_name": "Synthetic Patient",
    "date_of_birth": "1990-05-17",
    "phone": "+55 11 90000-0000",
    "email": "patient@example.test",
}


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app, headers=HTML) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


def form_token(html: str) -> str:
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def log_in(client, db_session, role: Role) -> None:
    account = StaffAccount(login=f"synthetic.{role.value}", role=role)
    account.set_password(PASSWORD)
    db_session.add(account)
    db_session.commit()
    token = form_token(client.get("/login").text)
    data = {"login": account.login, "password": PASSWORD, "csrf_token": token}
    assert client.post("/login", data=data, follow_redirects=False).status_code == 303


def submit(client, data):
    token = form_token(client.get("/patients/new").text)
    return client.post("/patients/new", data=data | {"csrf_token": token}, follow_redirects=False)


def input_tag(html: str, name: str) -> str:
    return re.search(rf'<input id="{name}"[^>]*>', html).group(0)


def text_of(html: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", html)).split())


@pytest.fixture
def receptionist(client, db_session):
    log_in(client, db_session, Role.RECEPTIONIST)


def test_patients_area_links_to_the_registration_form(client, receptionist):
    assert '<a href="/patients/new">Register a patient</a>' in client.get("/patients").text


def test_form_labels_every_field_and_marks_the_required_ones(client, receptionist):
    response = client.get("/patients/new")

    assert response.status_code == 200
    for name, label in [("full_name", "Full name"), ("date_of_birth", "Date of birth")]:
        assert (
            f'<label for="{name}">{label} <span class="required">(required)</span>' in response.text
        )
        assert 'aria-required="true"' in input_tag(response.text, name)
    for name, label in [("phone", "Phone"), ("email", "E-mail")]:
        assert f'<label for="{name}">{label}</label>' in response.text
    assert 'maxlength="120"' in input_tag(response.text, "full_name")
    assert 'min="1900-01-01"' in input_tag(response.text, "date_of_birth")
    assert "autofocus" in input_tag(response.text, "full_name")
    assert 'aria-current="true">Patients</a>' in response.text


def test_valid_registration_shows_the_record_with_a_confirmation(client, db_session, receptionist):
    response = submit(client, PATIENT)

    patient = db_session.scalars(select(Patient)).one()
    assert response.status_code == 303
    assert response.headers["location"] == f"/patients/{patient.id}?registered=1"
    page = text_of(client.get(response.headers["location"]).text)
    assert f"Patient registered with record number {patient.record_number}." in page
    assert (
        f"Record number {patient.record_number} Date of birth 1990-05-17 "
        "Phone +55 11 90000-0000 E-mail patient@example.test Status Active"
    ) in page


def test_record_without_contacts_and_without_the_confirmation(client, db_session, receptionist):
    submit(client, {"full_name": "Synthetic Patient", "date_of_birth": "1990-05-17"})
    patient = db_session.scalars(select(Patient)).one()

    page = text_of(client.get(f"/patients/{patient.id}").text)

    assert "Patient registered" not in page
    assert "Phone Not given E-mail Not given" in page


def test_invalid_registration_keeps_the_values_and_identifies_each_field(
    client, db_session, receptionist
):
    data = {"full_name": "", "date_of_birth": "", "phone": "12", "email": "patient@example.test"}

    response = submit(client, data)

    assert response.status_code == 422
    assert "<title>Error: Register a patient" in response.text
    summary = re.search(r'<div class="message error" role="alert".*?</div>', response.text, re.S)
    for name, key in [("full_name", "name_missing"), ("date_of_birth", "birth_missing")]:
        message = escape(MESSAGES[key])
        assert f'<a href="#{name}">{message}</a>' in summary.group(0)
        assert f'<p class="field-error" id="{name}-error">{message}</p>' in response.text
    phone = input_tag(response.text, "phone")
    assert 'aria-invalid="true"' in phone
    assert 'aria-describedby="phone-hint phone-error"' in phone
    assert 'value="12"' in phone
    assert 'value="patient@example.test"' in input_tag(response.text, "email")
    assert "aria-invalid" not in input_tag(response.text, "email")
    assert "autofocus" in input_tag(response.text, "full_name")
    assert db_session.scalar(select(func.count()).select_from(Patient)) == 0


def test_focus_moves_to_the_first_invalid_field(client, receptionist):
    response = submit(client, PATIENT | {"date_of_birth": "2999-01-01"})

    assert "autofocus" in input_tag(response.text, "date_of_birth")
    assert "autofocus" not in input_tag(response.text, "full_name")


@pytest.mark.parametrize("path", ["/patients/999999", "/patients/abc"])
def test_unknown_patient_records_are_not_found(client, receptionist, path):
    response = client.get(path)

    assert response.status_code == 404
    assert "Page not found" in response.text


@pytest.mark.parametrize("path", ["/patients/new", "/patients/1"])
def test_doctors_cannot_open_the_patient_pages(client, db_session, path):
    log_in(client, db_session, Role.DOCTOR)

    response = client.get(path)

    assert response.status_code == 403
    assert "Access denied" in response.text
