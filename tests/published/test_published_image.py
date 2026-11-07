"""Checks of an image published to GHCR (T-24.3, #148). Run with: pytest -m published"""

import os

import pytest

pytestmark = pytest.mark.published


def test_published_image_starts_after_the_migration_step(published_stack):
    migrate = published_stack.state("migrate")
    app = published_stack.state("app")

    assert migrate["State"] == "exited"
    assert migrate["ExitCode"] == 0
    assert app["State"] == "running"


def test_published_image_reports_healthy_with_database(published_stack):
    status, body = published_stack.get_health()

    assert status == 200
    assert body == {"status": "ok", "database": "ok"}


def test_published_image_serves_the_login_page(published_stack):
    status, body = published_stack.get("/login")

    assert status == 200
    assert "<h1>Log in</h1>" in body


def test_published_image_does_not_run_as_root(published_stack):
    uid = published_stack.compose("exec", "-T", "app", "id", "-u").stdout.strip()

    assert uid.isdigit()
    assert uid != "0"


def test_published_image_comes_from_this_repository(image_labels):
    source = image_labels["org.opencontainers.image.source"]

    assert source == "https://github.com/ceciliagalvaoo/hospital-devops"


@pytest.mark.skipif(not os.environ.get("EXPECTED_REVISION"), reason="EXPECTED_REVISION not set")
def test_published_image_revision_matches_the_commit(image_labels):
    assert image_labels["org.opencontainers.image.revision"] == os.environ["EXPECTED_REVISION"]


@pytest.mark.skipif(not os.environ.get("EXPECTED_VERSION"), reason="EXPECTED_VERSION not set")
def test_published_image_version_matches_the_build(image_labels):
    assert image_labels["org.opencontainers.image.version"] == os.environ["EXPECTED_VERSION"]
