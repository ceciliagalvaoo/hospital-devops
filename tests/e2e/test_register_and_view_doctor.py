"""End-to-end test of US-02 in a browser: register a doctor and view the profile (T-02.5).

Synthetic data only; the ``unlinked_doctor_account`` fixture deletes the profile and the
account afterwards.
"""

import re

import pytest
from playwright.sync_api import Page, expect
from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.doctors import MESSAGES
from app.models import Doctor, Role
from tests.e2e.browser import log_in

pytestmark = pytest.mark.e2e


def fill_range(page: Page, row: int, weekday: str, start: str, end: str) -> None:
    page.locator(f"#availability_{row}").select_option(label=weekday)
    page.locator(f"#start_time_{row}").fill(start)
    page.locator(f"#end_time_{row}").fill(end)


def profiles_of(db_engine: Engine, login: str) -> int:
    with Session(db_engine) as session:
        return session.scalar(
            select(func.count()).select_from(Doctor).where(Doctor.account.has(login=login))
        )


def test_register_a_doctor_and_view_the_profile(
    page: Page, e2e_accounts, unlinked_doctor_account, db_engine
):
    login = unlinked_doctor_account.login
    name = f"Dr Synthetic {login.rsplit('.', 1)[1]}"
    log_in(page, e2e_accounts[Role.ADMINISTRATOR])

    # From the navigation to the form, where the new account is offered.
    page.get_by_role("navigation", name="Main").get_by_role("link", name="Doctors").click()
    page.get_by_role("link", name="Register a doctor").click()
    expect(page).to_have_url(re.compile(r"/doctors/new$"))
    expect(page.get_by_label("Staff account")).to_contain_text(login)

    # Invalid data: no specialisation and two overlapping ranges on Monday.
    page.get_by_label("Staff account").select_option(label=login)
    page.get_by_label("Full name").fill(name)
    fill_range(page, 1, "Monday", "08:00", "12:00")
    fill_range(page, 2, "Monday", "11:00", "13:00")
    page.get_by_role("button", name="Register doctor").click()
    summary = page.get_by_role("alert")
    expect(summary).to_contain_text(MESSAGES["specialisation_invalid"])
    expect(summary).to_contain_text(MESSAGES["range_overlap"])
    expect(page).to_have_title(re.compile(r"^Error: Register a doctor"))
    assert page.evaluate("document.activeElement.id") == "specialisation"
    expect(page.locator("#availability_2-error")).to_have_text(MESSAGES["range_overlap"])
    expect(page.get_by_label("Full name")).to_have_value(name)
    assert profiles_of(db_engine, login) == 0

    # Corrected: a specialisation, adjacent Monday ranges and a Thursday afternoon.
    page.get_by_label("Specialisation").select_option(label="Paediatrics")
    fill_range(page, 2, "Monday", "12:00", "14:00")
    fill_range(page, 3, "Thursday", "13:30", "17:00")
    page.get_by_role("button", name="Register doctor").click()

    page.wait_for_url(re.compile(r"/doctors/\d+\?registered=1$"))
    expect(page.get_by_role("status")).to_have_text(
        f"Doctor registered and linked to the account {login}."
    )
    expect(page.get_by_role("heading", level=1)).to_have_text(name)
    expect(page.locator("dl.record")).to_contain_text("Paediatrics")
    expect(page.get_by_test_id("doctor-account")).to_have_text(login)
    rows = page.locator("tbody tr").all_inner_texts()
    assert [" ".join(row.split()) for row in rows] == [
        "Monday 08:00 12:00",
        "Monday 12:00 14:00",
        "Thursday 13:30 17:00",
    ]

    # The doctor is listed in the doctors area and opens the same profile.
    page.reload()
    page.get_by_role("link", name="Back to doctors").click()
    page.get_by_role("link", name=name).click()
    expect(page).to_have_url(re.compile(r"/doctors/\d+$"))
    expect(page.get_by_role("status")).to_have_count(0)
    expect(page.get_by_test_id("doctor-account")).to_have_text(login)
    assert profiles_of(db_engine, login) == 1

    # The account is no longer offered for a second profile.
    page.goto("/doctors/new")
    expect(page.get_by_label("Staff account")).not_to_contain_text(login)


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR], ids=str)
def test_receptionists_and_doctors_cannot_register_doctors(page: Page, e2e_accounts, role):
    log_in(page, e2e_accounts[role])

    navigation = page.get_by_role("navigation", name="Main")
    expect(navigation.get_by_role("link", name="Doctors")).to_have_count(0)
    response = page.goto("/doctors/new")

    assert response.status == 403
    expect(page.get_by_role("heading", level=1)).to_have_text("Access denied")
    expect(page.get_by_role("button", name="Register doctor")).to_have_count(0)
