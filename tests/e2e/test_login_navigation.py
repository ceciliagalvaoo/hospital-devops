"""End-to-end tests of login, role-based navigation and logout in a real browser (T-01.7)."""

import re

import pytest
from playwright.sync_api import Page, expect

from app.models import Role

pytestmark = pytest.mark.e2e

# Written out from the RBAC matrix (README §3.2) instead of read from app.navigation.
AREA_PATHS = {
    "Patients": "/patients",
    "Doctors": "/doctors",
    "Appointments": "/appointments",
    "Medical records": "/records",
    "Staff accounts": "/staff",
}
ALLOWED = {
    Role.RECEPTIONIST: ["Patients", "Appointments"],
    Role.DOCTOR: ["Appointments", "Medical records"],
    Role.ADMINISTRATOR: ["Patients", "Doctors", "Appointments", "Staff accounts"],
}


def log_in(page: Page, login: str, password: str) -> None:
    page.goto("/login")
    page.get_by_label("Login", exact=True).fill(login)
    page.get_by_label("Password", exact=True).fill(password)
    page.get_by_role("button", name="Log in").click()


@pytest.mark.parametrize("role", list(Role), ids=str)
def test_each_role_logs_in_navigates_its_areas_and_logs_out(page: Page, e2e_accounts, role):
    account = e2e_accounts[role]

    log_in(page, account.login, account.password)

    expect(page).to_have_url(re.compile(r"/$"))
    expect(page.get_by_test_id("current-account")).to_have_text(f"{account.login} ({role.value})")
    navigation = page.get_by_role("navigation", name="Main")
    expect(navigation.get_by_role("link")).to_have_text(["Home", *ALLOWED[role]])

    for title in ALLOWED[role]:
        navigation.get_by_role("link", name=title, exact=True).click()
        expect(page).to_have_url(re.compile(f"{AREA_PATHS[title]}$"))
        expect(page.get_by_role("heading", level=1)).to_have_text(title)

    for title in AREA_PATHS.keys() - set(ALLOWED[role]):
        response = page.goto(AREA_PATHS[title])
        assert response is not None and response.status == 403
        expect(page.get_by_role("heading", level=1)).to_have_text("Access denied")

    page.get_by_role("button", name="Log out").click()

    expect(page).to_have_url(re.compile(r"/login$"))
    response = page.goto("/")
    assert response is not None and response.status == 401
    expect(page.get_by_role("status")).to_have_text("Please log in to continue.")


def test_wrong_password_shows_the_error_message(page: Page, e2e_accounts):
    log_in(page, e2e_accounts[Role.DOCTOR].login, "wrong-password")

    expect(page).to_have_url(re.compile(r"/login$"))
    expect(page.get_by_role("alert")).to_have_text("Invalid login or password.")
    expect(page.get_by_label("Login", exact=True)).to_have_value(e2e_accounts[Role.DOCTOR].login)
    expect(page.get_by_label("Password", exact=True)).to_have_value("")


def test_protected_page_without_a_session_shows_the_login_page(page: Page, e2e_accounts):
    response = page.goto("/appointments")

    assert response is not None and response.status == 401
    expect(page.get_by_role("heading", level=1)).to_have_text("Log in")
    expect(page.get_by_role("status")).to_have_text("Please log in to continue.")
