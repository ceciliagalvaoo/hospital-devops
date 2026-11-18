"""End-to-end test of US-09 in a browser: register patients, search and open the correct
record (T-09.4). It also covers, in a browser, the search criterion of US-03.

Synthetic data only; the ``patient_name`` fixture deletes the patients afterwards.
"""

import re

import pytest
from playwright.sync_api import Page, expect

from app.models import Role
from app.patients import SEARCH_MESSAGES
from tests.e2e.browser import log_in, register_patient

pytestmark = pytest.mark.e2e


def search(page: Page, query: str) -> None:
    page.get_by_label("Search by name or record number").fill(query)
    page.get_by_label("Search by name or record number").press("Enter")
    page.wait_for_load_state()


def listed(page: Page) -> list[str]:
    return [row.inner_text().split("\t")[1] for row in page.locator("tbody tr").all()]


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.ADMINISTRATOR], ids=str)
def test_register_search_and_open_the_correct_record(page: Page, e2e_accounts, patient_name, role):
    alpha, beta = f"{patient_name} Alpha", f"{patient_name} Beta"
    log_in(page, e2e_accounts[role])
    alpha_number = register_patient(page, alpha)
    beta_number = register_patient(page, beta, "1985-01-02")

    # Search from the patients area, reached through the navigation.
    page.get_by_role("navigation", name="Main").get_by_role("link", name="Patients").click()
    search(page, patient_name.lower())
    expect(page.locator("#search-summary")).to_have_text(
        f'2 patients found for "{patient_name.lower()}".'
    )
    assert listed(page) == [alpha, beta]

    # With two patients listed, the second name opens the second patient's record.
    page.get_by_role("link", name=beta).click()
    expect(page).to_have_url(re.compile(r"/patients/\d+$"))
    expect(page.get_by_role("heading", level=1)).to_have_text(beta)
    expect(page.get_by_test_id("record-number")).to_have_text(beta_number)
    expect(page.locator("dl.record")).to_contain_text("1985-01-02")
    expect(page.get_by_role("status")).to_have_count(0)  # no registration confirmation

    # Several words narrow the search; the record number finds exactly that patient.
    page.get_by_role("link", name="Back to patients").click()
    search(page, f"beta {patient_name.split()[-1]}")
    assert listed(page) == [beta]
    search(page, alpha_number)
    assert listed(page) == [alpha]
    page.get_by_role("link", name=alpha).click()
    expect(page.get_by_test_id("record-number")).to_have_text(alpha_number)

    # A search without matches shows the empty state, and an unusable one its message.
    page.get_by_role("link", name="Back to patients").click()
    search(page, f"{patient_name} Gamma")
    expect(page.get_by_role("status")).to_contain_text(f'No patients match "{patient_name} Gamma".')
    expect(page.get_by_role("table")).to_have_count(0)
    search(page, "a")
    expect(page.get_by_role("alert")).to_have_text(SEARCH_MESSAGES["too_short"])
    assert page.evaluate("document.activeElement.id") == "q"


def test_doctors_cannot_search_patients(page: Page, e2e_accounts):
    log_in(page, e2e_accounts[Role.DOCTOR])

    navigation = page.get_by_role("navigation", name="Main")
    expect(navigation.get_by_role("link", name="Patients")).to_have_count(0)
    response = page.goto("/patients?q=synthetic")

    assert response.status == 403
    expect(page.get_by_role("heading", level=1)).to_have_text("Access denied")
    expect(page.get_by_role("search")).to_have_count(0)
