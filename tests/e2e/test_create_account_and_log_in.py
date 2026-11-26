"""End-to-end test of US-14 in a browser: create a staff account and log in with its role
(T-14.4). Synthetic data only; the ``new_account_login`` fixture deletes the account."""

import re

import pytest
from playwright.sync_api import Page, expect
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.accounts import MESSAGES
from app.models import Role, StaffAccount
from tests.e2e.browser import log_in

pytestmark = pytest.mark.e2e

NEW_PASSWORD = "synthetic-e2e-new-password"
AREAS = {"Patients", "Doctors", "Appointments", "Medical records", "Staff accounts"}


def stored_account(db_engine: Engine, login: str) -> StaffAccount | None:
    with Session(db_engine) as session:
        return session.scalar(select(StaffAccount).where(StaffAccount.login == login))


def test_create_an_account_and_log_in_with_its_role(
    page: Page, e2e_accounts, db_engine, new_account_login
):
    typed_login = new_account_login.upper()  # stored in lower case
    log_in(page, e2e_accounts[Role.ADMINISTRATOR])

    # From the navigation to the form.
    page.get_by_role("navigation", name="Main").get_by_role("link", name="Staff accounts").click()
    page.get_by_role("link", name="Create a staff account").click()
    expect(page).to_have_url(re.compile(r"/staff/new$"))

    # Passwords that do not match are identified, and nothing is created.
    page.get_by_label("Login").fill(typed_login)
    page.get_by_label("Role").select_option(label="Doctor")
    page.locator("#password").fill(NEW_PASSWORD)  # labelled "Password (required)"
    page.get_by_label("Repeat the password").fill("another-password-1")
    page.get_by_role("button", name="Create account").click()
    expect(page.get_by_role("alert")).to_contain_text(MESSAGES["password_mismatch"])
    expect(page.get_by_label("Login")).to_have_value(typed_login)
    expect(page.locator("#password")).to_have_value("")  # never sent back
    assert stored_account(db_engine, new_account_login) is None

    # Corrected, the account is created and shown in the list.
    page.locator("#password").fill(NEW_PASSWORD)
    page.get_by_label("Repeat the password").fill(NEW_PASSWORD)
    page.get_by_role("button", name="Create account").click()
    page.wait_for_url(re.compile(r"/staff\?created=\d+$"))
    expect(page.get_by_role("status")).to_have_text(
        f"Account {new_account_login} created with the role doctor."
    )
    expect(page.locator("tr.highlight")).to_contain_text(new_account_login)
    created = stored_account(db_engine, new_account_login)
    assert created.role is Role.DOCTOR
    assert created.password_hash.startswith("$2b$12$")

    # The administrator logs out and the new account logs in with its role.
    page.get_by_role("button", name="Log out").click()
    page.wait_for_url("**/login")
    page.get_by_label("Login", exact=True).fill(typed_login)  # any case logs in
    page.get_by_label("Password", exact=True).fill(NEW_PASSWORD)
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url("**/")
    expect(page.get_by_test_id("current-account")).to_have_text(f"{new_account_login} (doctor)")
    navigation = page.get_by_role("navigation", name="Main")
    shown = {name for name in AREAS if navigation.get_by_role("link", name=name).count()}
    assert shown == {"Appointments", "Medical records"}
    assert page.goto("/staff").status == 403


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR], ids=str)
def test_receptionists_and_doctors_cannot_create_accounts(page: Page, e2e_accounts, role):
    log_in(page, e2e_accounts[role])

    navigation = page.get_by_role("navigation", name="Main")
    expect(navigation.get_by_role("link", name="Staff accounts")).to_have_count(0)
    response = page.goto("/staff/new")

    assert response.status == 403
    expect(page.get_by_role("heading", level=1)).to_have_text("Access denied")
    expect(page.get_by_role("button", name="Create account")).to_have_count(0)
