"""Browser steps shared by the end-to-end tests."""

import re

from playwright.sync_api import Page, expect


def log_in(page: Page, account) -> None:
    page.goto("/login")
    page.get_by_label("Login", exact=True).fill(account.login)
    page.get_by_label("Password", exact=True).fill(account.password)
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url("**/")


def register_patient(
    page: Page, full_name: str, date_of_birth: str = "1990-05-17", phone: str = "", email: str = ""
) -> str:
    """Register a patient through the form and return its record number."""
    page.goto("/patients/new")
    page.get_by_label("Full name").fill(full_name)
    page.get_by_label("Date of birth").fill(date_of_birth)
    page.get_by_label("Phone").fill(phone)
    page.get_by_label("E-mail").fill(email)
    page.get_by_role("button", name="Register patient").click()
    page.wait_for_url(re.compile(r"/patients/\d+\?registered=1$"))
    expect(page.get_by_role("heading", level=1)).to_have_text(full_name)
    return page.get_by_test_id("record-number").inner_text()
