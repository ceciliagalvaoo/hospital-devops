"""End-to-end test of US-15 in a browser: deactivate a staff account and verify that its
access is refused (T-15.4). Two browser contexts are used: the account being deactivated
stays logged in in one while an administrator deactivates it in the other. Synthetic data
only; the ``receptionist_to_deactivate`` fixture deletes the account."""

import re

import pytest
from playwright.sync_api import Browser, Page, expect
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.models import Role, StaffAccount, StaffSession
from app.routes.auth import INVALID_CREDENTIALS
from tests.e2e.browser import log_in

pytestmark = pytest.mark.e2e


def account_state(db_engine: Engine, login: str) -> tuple[bool, int]:
    """Whether the account is active, and how many sessions it has."""
    with Session(db_engine) as session:
        staff = session.scalar(select(StaffAccount).where(StaffAccount.login == login))
        sessions = session.scalar(
            select(func.count())
            .select_from(StaffSession)
            .where(StaffSession.staff_account_id == staff.id)
        )
        return staff.is_active, sessions


def test_deactivate_an_account_and_its_access_is_refused(
    page: Page, browser: Browser, base_url, e2e_accounts, receptionist_to_deactivate, db_engine
):
    login = receptionist_to_deactivate.login
    # The receptionist is logged in and working in its own browser.
    receptionist = browser.new_context(base_url=base_url).new_page()
    log_in(receptionist, receptionist_to_deactivate)
    receptionist.goto("/patients")
    expect(receptionist.get_by_role("heading", level=1)).to_have_text("Patients")
    assert account_state(db_engine, login) == (True, 1)

    # The administrator finds the account in the list and opens its confirmation.
    log_in(page, e2e_accounts[Role.ADMINISTRATOR])
    page.get_by_role("navigation", name="Main").get_by_role("link", name="Staff accounts").click()
    expect(page.get_by_role("row", name=re.compile(rf"^{re.escape(login)} "))).to_contain_text(
        "Active"
    )
    page.get_by_role("link", name=f"Deactivate {login}").click()
    expect(page.get_by_role("heading", level=1)).to_have_text(f"Deactivate {login}")
    expect(page.get_by_text("It can no longer log in.")).to_be_visible()

    # Cancelling changes nothing; the receptionist keeps working.
    page.get_by_role("link", name="Cancel").click()
    expect(page).to_have_url(re.compile(r"/staff$"))
    receptionist.reload()
    expect(receptionist.get_by_role("heading", level=1)).to_have_text("Patients")

    # Confirmed, the account is deactivated and the list says so.
    page.get_by_role("link", name=f"Deactivate {login}").click()
    page.get_by_role("button", name="Deactivate account").click()
    page.wait_for_url(re.compile(r"/staff\?deactivated=\d+$"))
    expect(page.get_by_role("status")).to_have_text(
        f"Account {login} deactivated. It can no longer log in."
    )
    row = page.locator("tr.highlight")
    expect(row).to_contain_text(login)
    expect(row).to_contain_text("Inactive")
    expect(page.get_by_role("link", name=f"Deactivate {login}")).to_have_count(0)
    assert account_state(db_engine, login) == (False, 0)

    # The receptionist's open session is rejected at its next request.
    response = receptionist.goto("/patients")
    assert response.status == 401
    expect(receptionist.get_by_text("Please log in to continue.")).to_be_visible()
    expect(receptionist.get_by_test_id("current-account")).to_have_count(0)

    # Logging in again is refused like a wrong password.
    receptionist.get_by_label("Login", exact=True).fill(login)
    receptionist.get_by_label("Password", exact=True).fill(receptionist_to_deactivate.password)
    receptionist.get_by_role("button", name="Log in").click()
    expect(receptionist.get_by_role("alert")).to_have_text(INVALID_CREDENTIALS)
    expect(receptionist).to_have_url(re.compile(r"/login$"))
    assert account_state(db_engine, login) == (False, 0)
    receptionist.context.close()


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR], ids=str)
def test_receptionists_and_doctors_cannot_deactivate_accounts(
    page: Page, e2e_accounts, receptionist_to_deactivate, db_engine, role
):
    log_in(page, e2e_accounts[role])

    expect(
        page.get_by_role("navigation", name="Main").get_by_role("link", name="Staff accounts")
    ).to_have_count(0)
    with Session(db_engine) as session:
        target_id = session.scalar(
            select(StaffAccount.id).where(StaffAccount.login == receptionist_to_deactivate.login)
        )
    response = page.goto(f"/staff/{target_id}/deactivate")

    assert response.status == 403
    expect(page.get_by_role("heading", level=1)).to_have_text("Access denied")
    expect(page.get_by_role("button", name="Deactivate account")).to_have_count(0)
    assert account_state(db_engine, receptionist_to_deactivate.login) == (True, 0)
