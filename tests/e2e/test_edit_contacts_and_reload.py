"""End-to-end test of US-10 in a browser: edit a patient's contact details and reload the
record (T-10.4). Synthetic data only; the ``patient_name`` fixture deletes the patients
afterwards.
"""

import re
from datetime import date

import pytest
from playwright.sync_api import Page, expect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models import Patient, Role
from app.patients import MESSAGES
from tests.e2e.browser import log_in, register_patient

pytestmark = pytest.mark.e2e

OLD_PHONE, OLD_EMAIL = "+55 11 90000-0000", "old.address@example.test"
NEW_PHONE = "+55 21 98888-7777"


def record_values(page: Page) -> dict[str, str]:
    terms = page.locator("dl.record dt").all_inner_texts()
    return dict(zip(terms, page.locator("dl.record dd").all_inner_texts(), strict=True))


def stored_contacts(db_engine: Engine, full_name: str) -> tuple:
    with Session(db_engine) as session:
        patient = session.query(Patient).filter_by(full_name=full_name).one()
        return (patient.phone, patient.email)


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.ADMINISTRATOR], ids=str)
def test_edit_contacts_and_reload_the_record(
    page: Page, e2e_accounts, db_engine, patient_name, role
):
    log_in(page, e2e_accounts[role])
    register_patient(page, patient_name, phone=OLD_PHONE, email=OLD_EMAIL)
    record_url = page.url.split("?")[0]

    # From the record to the form, which shows the current contacts.
    page.get_by_role("link", name="Edit contact details").click()
    expect(page).to_have_url(re.compile(r"/patients/\d+/contacts$"))
    expect(page.get_by_label("Phone")).to_have_value(OLD_PHONE)
    expect(page.get_by_label("E-mail")).to_have_value(OLD_EMAIL)
    assert page.evaluate("document.activeElement.id") == "phone"

    # An invalid e-mail is identified, keeps what was typed and saves nothing.
    page.get_by_label("Phone").fill(NEW_PHONE)
    page.get_by_label("E-mail").fill("not-an-address")
    page.get_by_role("button", name="Save contact details").click()
    expect(page.get_by_role("alert")).to_contain_text(MESSAGES["email_invalid"])
    expect(page).to_have_title(re.compile(r"^Error: Edit contact details"))
    expect(page.get_by_label("Phone")).to_have_value(NEW_PHONE)
    assert page.evaluate("document.activeElement.id") == "email"
    assert stored_contacts(db_engine, patient_name) == (OLD_PHONE, OLD_EMAIL)

    # A new phone and an emptied e-mail are saved and shown with a confirmation.
    page.get_by_label("E-mail").fill("")
    page.get_by_role("button", name="Save contact details").click()
    page.wait_for_url(re.compile(r"/patients/\d+\?updated=1$"))
    expect(page.get_by_role("status")).to_have_text("Contact details saved.")
    assert record_values(page)["Phone"] == NEW_PHONE
    assert record_values(page)["E-mail"] == "Not given"

    # Reloading the record, and opening it again later, shows the saved details.
    page.reload()
    assert record_values(page)["Phone"] == NEW_PHONE
    page.goto(record_url)
    expect(page.get_by_role("status")).to_have_count(0)
    assert (record_values(page)["Phone"], record_values(page)["E-mail"]) == (
        NEW_PHONE,
        "Not given",
    )
    assert stored_contacts(db_engine, patient_name) == (NEW_PHONE, None)


def test_doctors_cannot_edit_contacts(page: Page, e2e_accounts, db_engine, patient_name):
    with Session(db_engine) as session:
        patient = Patient(full_name=patient_name, date_of_birth=date(1990, 5, 17), phone=OLD_PHONE)
        session.add(patient)
        session.commit()
        patient_id = patient.id
    log_in(page, e2e_accounts[Role.DOCTOR])

    response = page.goto(f"/patients/{patient_id}/contacts")

    assert response.status == 403
    expect(page.get_by_role("heading", level=1)).to_have_text("Access denied")
    expect(page.get_by_label("Phone")).to_have_count(0)
    assert stored_contacts(db_engine, patient_name) == (OLD_PHONE, None)
