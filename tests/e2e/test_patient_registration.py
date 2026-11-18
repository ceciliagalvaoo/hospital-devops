"""End-to-end test of US-03 in a browser: register a patient and see the saved record (T-03.5).

Synthetic data only. Each run uses a unique patient name and deletes its patients afterwards,
because the live server commits to the test database.
"""

import re
import uuid

import pytest
from playwright.sync_api import Page, expect
from sqlalchemy import delete, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models import Patient, Role
from app.patients import MESSAGES

pytestmark = pytest.mark.e2e


@pytest.fixture
def patient_name(db_engine: Engine):
    name = f"E2E Synthetic Patient {uuid.uuid4().hex[:8]}"
    yield name
    with Session(db_engine) as session:
        session.execute(delete(Patient).where(Patient.full_name == name))
        session.commit()


def saved_with_name(db_engine: Engine, name: str) -> int:
    with Session(db_engine) as session:
        return session.scalar(select(func.count()).where(Patient.full_name == name))


def log_in(page: Page, account) -> None:
    page.goto("/login")
    page.get_by_label("Login", exact=True).fill(account.login)
    page.get_by_label("Password", exact=True).fill(account.password)
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url("**/")


def focused_field(page: Page) -> str:
    return page.evaluate("document.activeElement.id")


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.ADMINISTRATOR], ids=str)
def test_register_a_patient_and_display_the_saved_record(
    page: Page, e2e_accounts, db_engine, patient_name, role
):
    log_in(page, e2e_accounts[role])

    # From the navigation to the form, as a user would.
    page.get_by_role("navigation", name="Main").get_by_role("link", name="Patients").click()
    page.get_by_role("link", name="Register a patient").click()
    expect(page).to_have_url(re.compile(r"/patients/new$"))
    assert focused_field(page) == "full_name"

    # Submitting the empty form identifies both missing fields and saves nothing.
    page.get_by_role("button", name="Register patient").click()
    summary = page.get_by_role("alert")
    expect(summary).to_contain_text(MESSAGES["name_missing"])
    expect(summary).to_contain_text(MESSAGES["birth_missing"])
    expect(page).to_have_title(re.compile(r"^Error: Register a patient"))
    assert focused_field(page) == "full_name"

    # Corrected data is saved and the record is displayed with a confirmation.
    page.get_by_label("Full name").fill(patient_name)
    page.get_by_label("Date of birth").fill("1990-05-17")
    page.get_by_label("Phone").fill("+55 11 90000-0000")
    page.get_by_label("E-mail").fill("patient@example.test")
    page.get_by_role("button", name="Register patient").click()

    page.wait_for_url(re.compile(r"/patients/\d+\?registered=1$"))
    record_number = page.get_by_test_id("record-number").inner_text()
    assert re.fullmatch(r"P-\d{6,}", record_number)
    expect(page.get_by_role("status")).to_have_text(
        f"Patient registered with record number {record_number}."
    )
    expect(page.get_by_role("heading", level=1)).to_have_text(patient_name)
    record = page.locator("dl.record")
    for text in ["1990-05-17", "+55 11 90000-0000", "patient@example.test", "Active"]:
        expect(record).to_contain_text(text)

    # Reloading the confirmation does not register the patient a second time.
    page.reload()
    expect(page.get_by_role("heading", level=1)).to_have_text(patient_name)
    assert saved_with_name(db_engine, patient_name) == 1


def test_doctors_cannot_register_patients(page: Page, e2e_accounts):
    log_in(page, e2e_accounts[Role.DOCTOR])

    navigation = page.get_by_role("navigation", name="Main")
    expect(navigation.get_by_role("link", name="Patients")).to_have_count(0)
    response = page.goto("/patients/new")

    assert response.status == 403
    expect(page.get_by_role("heading", level=1)).to_have_text("Access denied")
    expect(page.get_by_role("button", name="Register patient")).to_have_count(0)
