"""Deliberately failing end-to-end test, used to verify the failure artifacts of the CI job.

It runs only when CI_FORCE_FAILURE=true, which is set by a manual CI run with
``force_failure=true`` (README §11), like the deliberate failure of the Tests job.
"""

import os

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e


@pytest.mark.skipif(
    os.environ.get("CI_FORCE_FAILURE") != "true",
    reason="Deliberate failure runs only when CI_FORCE_FAILURE=true (manual CI run).",
)
def test_deliberate_failure_keeps_a_screenshot_video_and_trace(page: Page, live_server):
    page.goto("/login")

    expect(page.get_by_role("heading", level=1)).to_have_text(
        "Deliberate failure requested with CI_FORCE_FAILURE=true", timeout=1000
    )
