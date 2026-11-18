"""Integration tests for the contact-edit form and its save confirmation (T-10.2).

Synthetic data only. The acceptance and access tests of US-10 are T-10.3 (#45).
"""

import re
from datetime import date
from html import unescape

import pytest
from fastapi.testclient import TestClient
from markupsafe import escape

from app.db import get_session
from app.main import app
from app.models import Patient, Role, StaffAccount
from app.patients import MESSAGES

PASSWORD = "synthetic-password"
HTML = {"Accept": "text/html"}
OLD = ("+55 11 90000-0000", "old.address@example.test")


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app, headers=HTML) as test_client:
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


def form_token(html: str) -> str:
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def log_in(client, db_session, role: Role) -> None:
    account = StaffAccount(login=f"synthetic.{role.value}", role=role)
    account.set_password(PASSWORD)
    db_session.add(account)
    db_session.commit()
    data = {
        "login": account.login,
        "password": PASSWORD,
        "csrf_token": form_token(client.get("/login").text),
    }
    assert client.post("/login", data=data, follow_redirects=False).status_code == 303


@pytest.fixture
def receptionist(client, db_session):
    log_in(client, db_session, Role.RECEPTIONIST)


def submit(client, patient, data):
    token = form_token(client.get("/login").text)
    return client.post(
        f"/patients/{patient.id}/contacts",
        data=data | {"csrf_token": token},
        follow_redirects=False,
    )


def input_tag(html: str, name: str) -> str:
    return re.search(rf'<input id="{name}"[^>]*>', html).group(0)


def text_of(html: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", html)).split())


def stored(db_session, patient) -> tuple:
    db_session.expire_all()
    return (patient.phone, patient.email)


def test_the_record_links_to_the_contact_form(client, receptionist, patient):
    page = client.get(f"/patients/{patient.id}").text

    assert f'<a href="/patients/{patient.id}/contacts">Edit contact details</a>' in page


def test_the_form_shows_the_patient_and_the_current_contacts(client, receptionist, patient):
    response = client.get(f"/patients/{patient.id}/contacts")

    assert response.status_code == 200
    assert "<title>Edit contact details" in response.text
    assert f"Synthetic Patient, record number {patient.record_number}" in text_of(response.text)
    assert f'value="{OLD[0]}"' in input_tag(response.text, "phone")
    assert f'value="{OLD[1]}"' in input_tag(response.text, "email")
    assert '<label for="phone">Phone</label>' in response.text
    assert '<label for="email">E-mail</label>' in response.text
    assert "Leave empty to remove it." in response.text
    assert "autofocus" in input_tag(response.text, "phone")
    assert f'<a href="/patients/{patient.id}">Cancel</a>' in response.text


def test_saving_shows_the_record_with_a_confirmation(client, db_session, receptionist, patient):
    response = submit(client, patient, {"phone": "+55 21 98888-7777", "email": "new@example.test"})

    assert response.status_code == 303
    assert response.headers["location"] == f"/patients/{patient.id}?updated=1"
    page = text_of(client.get(response.headers["location"]).text)
    assert "Contact details saved." in page
    assert "Phone +55 21 98888-7777 E-mail new@example.test" in page
    assert stored(db_session, patient) == ("+55 21 98888-7777", "new@example.test")


def test_empty_fields_remove_the_contacts(client, db_session, receptionist, patient):
    submit(client, patient, {"phone": "", "email": ""})

    page = text_of(client.get(f"/patients/{patient.id}").text)
    assert "Phone Not given E-mail Not given" in page
    assert "Contact details saved." not in page  # the confirmation is shown only after saving
    assert stored(db_session, patient) == (None, None)


def test_invalid_contacts_keep_the_values_identify_the_fields_and_change_nothing(
    client, db_session, receptionist, patient
):
    response = submit(client, patient, {"phone": "+55 21 98888-7777", "email": "nope"})

    assert response.status_code == 422
    assert "<title>Error: Edit contact details" in response.text
    summary = re.search(r'<div class="message error" role="alert".*?</div>', response.text, re.S)
    assert "The contact details were not saved. Check these fields:" in summary.group(0)
    message = escape(MESSAGES["email_invalid"])
    assert f'<a href="#email">{message}</a>' in summary.group(0)
    assert f'<p class="field-error" id="email-error">{message}</p>' in response.text
    email = input_tag(response.text, "email")
    assert 'value="nope"' in email
    assert 'aria-invalid="true"' in email
    assert "autofocus" in email  # the first invalid field
    phone = input_tag(response.text, "phone")
    assert 'value="+55 21 98888-7777"' in phone
    assert "aria-invalid" not in phone
    assert "autofocus" not in phone
    assert stored(db_session, patient) == OLD


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_unknown_patients_are_not_found(client, receptionist, method):
    token = form_token(client.get("/login").text)
    response = client.request(method, "/patients/999999/contacts", data={"csrf_token": token})

    assert response.status_code == 404
    assert "Page not found" in response.text


@pytest.mark.parametrize("method", ["GET", "POST"])
def test_doctors_cannot_edit_contacts(client, db_session, patient, method):
    log_in(client, db_session, Role.DOCTOR)
    token = form_token(client.get("/login").text)

    response = client.request(
        method,
        f"/patients/{patient.id}/contacts",
        data={"phone": "", "email": "", "csrf_token": token},
    )

    assert response.status_code == 403
    assert "Access denied" in response.text
    assert stored(db_session, patient) == OLD
