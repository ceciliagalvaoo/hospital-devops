"""End-to-end check that the pages fit a 320 px wide screen without horizontal scrolling.

Reproduces #202: a long login in the home page heading made the page wider than the screen.
"""

import pytest
from playwright.sync_api import Page

from app.models import Role

pytestmark = pytest.mark.e2e

SMALL_SCREEN = {"width": 320, "height": 640}
SCROLLS_HORIZONTALLY = "document.documentElement.scrollWidth > document.documentElement.clientWidth"
PAGES = ["/", "/patients", "/doctors", "/appointments", "/records", "/staff", "/no-such-page"]


def assert_fits(page: Page, description: str) -> None:
    assert not page.evaluate(SCROLLS_HORIZONTALLY), f"{description} scrolls horizontally"


@pytest.mark.parametrize("role", list(Role), ids=str)
def test_pages_fit_a_320_px_screen(page: Page, e2e_accounts, role):
    account = e2e_accounts[role]
    page.set_viewport_size(SMALL_SCREEN)

    page.goto("/login")
    assert_fits(page, "the login page")
    page.get_by_label("Login", exact=True).fill(account.login)
    page.get_by_label("Password", exact=True).fill("wrong-password")
    page.get_by_role("button", name="Log in").click()
    assert_fits(page, "the login error")
    page.get_by_label("Password", exact=True).fill(account.password)
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url("**/")

    for path in PAGES:  # includes the areas of other roles and the not-found page
        page.goto(path)
        assert_fits(page, f"{path} for {role.value}")


def test_long_login_fits_a_320_px_screen(page: Page, e2e_long_login_account):
    # The longest login a staff account can have (64 characters) has no break opportunities.
    page.set_viewport_size(SMALL_SCREEN)
    page.goto("/login")
    page.get_by_label("Login", exact=True).fill(e2e_long_login_account.login)
    page.get_by_label("Password", exact=True).fill(e2e_long_login_account.password)
    page.get_by_role("button", name="Log in").click()
    page.wait_for_url("**/")

    assert_fits(page, "the home page with a 64-character login")
