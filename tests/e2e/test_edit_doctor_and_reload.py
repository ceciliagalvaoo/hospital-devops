"""End-to-end test of US-13 in a browser: update a doctor's details and availability and
reload them (T-13.4). Synthetic data only; the fixtures delete the profile and its account."""

import re
from datetime import time

import pytest
from playwright.sync_api import Page, expect
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.doctors import MESSAGES
from app.models import Doctor, Role, Specialisation, Weekday
from tests.e2e.browser import log_in

pytestmark = pytest.mark.e2e


def stored(db_engine: Engine, doctor_id: int) -> tuple:
    with Session(db_engine) as session:
        doctor = session.get(Doctor, doctor_id)
        ranges = [(r.weekday, r.start_time, r.end_time) for r in doctor.availability]
        return (doctor.full_name, doctor.specialisation, doctor.is_active, ranges)


def table_rows(page: Page) -> list[str]:
    return [" ".join(row.split()) for row in page.locator("table tbody tr").all_inner_texts()]


def test_update_a_doctor_and_reload_the_details(
    page: Page, e2e_accounts, unlinked_doctor_account, doctor_profile, db_engine
):
    before = stored(db_engine, doctor_profile)
    log_in(page, e2e_accounts[Role.ADMINISTRATOR])

    # From the doctors area to the profile and its edit form, filled in with the current values.
    page.get_by_role("navigation", name="Main").get_by_role("link", name="Doctors").click()
    page.get_by_role("link", name="Dr Synthetic Edit").click()
    page.get_by_role("link", name="Edit doctor details").click()
    expect(page).to_have_url(re.compile(rf"/doctors/{doctor_profile}/edit$"))
    expect(page.get_by_text(f"staff account {unlinked_doctor_account.login}")).to_be_visible()
    expect(page.get_by_label("Full name")).to_have_value("Dr Synthetic Edit")
    expect(page.get_by_label("Specialisation")).to_have_value("cardiology")
    expect(page.locator("#availability_1")).to_have_value("0")
    expect(page.locator("#start_time_1")).to_have_value("08:00")
    expect(page.locator("#availability_2")).to_have_value("2")
    expect(page.locator("#end_time_2")).to_have_value("18:00")

    # Invalid availability: a Wednesday range overlapping the existing one, identified at row 3.
    page.get_by_label("Full name").fill("Dr Synthetic Edited")
    page.get_by_label("Specialisation").select_option(label="Neurology")
    page.locator("#availability_3").select_option(label="Wednesday")
    page.locator("#start_time_3").fill("17:00")
    page.locator("#end_time_3").fill("19:00")
    page.get_by_role("button", name="Save changes").click()
    expect(page).to_have_title(re.compile(r"^Error: Edit doctor details"))
    expect(page.get_by_role("alert")).to_contain_text(MESSAGES["range_overlap"])
    expect(page.locator("#availability_3-error")).to_have_text(MESSAGES["range_overlap"])
    expect(page.get_by_label("Full name")).to_have_value("Dr Synthetic Edited")  # kept
    assert stored(db_engine, doctor_profile) == before  # nothing saved

    # Corrected: Monday removed, the new range moved after the existing one.
    page.locator("#availability_1").select_option(index=0)
    page.locator("#start_time_1").fill("")
    page.locator("#end_time_1").fill("")
    page.locator("#start_time_3").fill("18:00")
    page.get_by_role("button", name="Save changes").click()
    page.wait_for_url(re.compile(rf"/doctors/{doctor_profile}\?updated=1$"))
    expect(page.get_by_role("status")).to_have_text("Doctor details saved.")

    # Reloaded, the profile and the edit form show what the database holds.
    page.goto(f"/doctors/{doctor_profile}")
    expect(page.get_by_role("status")).to_have_count(0)
    expect(page.get_by_role("heading", level=1)).to_have_text("Dr Synthetic Edited")
    expect(page.get_by_role("main")).to_contain_text("Neurology")
    expect(page.get_by_role("main")).not_to_contain_text("Cardiology")
    assert table_rows(page) == ["Wednesday 14:00 18:00", "Wednesday 18:00 19:00"]
    page.get_by_role("link", name="Edit doctor details").click()
    expect(page.locator("#availability_1")).to_have_value("2")
    expect(page.locator("#start_time_2")).to_have_value("18:00")
    expect(page.locator("#availability_3")).to_have_value("")
    assert stored(db_engine, doctor_profile) == (
        "Dr Synthetic Edited",
        Specialisation.NEUROLOGY,
        True,
        [(Weekday.WEDNESDAY, time(14), time(18)), (Weekday.WEDNESDAY, time(18), time(19))],
    )


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR], ids=str)
def test_receptionists_and_doctors_cannot_edit_doctors(
    page: Page, e2e_accounts, doctor_profile, role
):
    log_in(page, e2e_accounts[role])

    response = page.goto(f"/doctors/{doctor_profile}/edit")

    assert response.status == 403
    expect(page.get_by_role("heading", level=1)).to_have_text("Access denied")
    expect(page.get_by_role("button", name="Save changes")).to_have_count(0)
