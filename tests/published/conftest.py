"""Fixtures for the checks of a published image (T-24.3, #148).

Run against an image in the registry, preferably by its immutable commit tag:

    PUBLISHED_IMAGE=ghcr.io/ceciliagalvaoo/hospital-devops:sha-<commit> \\
    EXPECTED_REVISION=<full commit SHA> pytest -m published
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.compose_stack import ComposeStack

PUBLISHED_IMAGE_FILE = Path(__file__).with_name("compose.published-image.yml")


@pytest.fixture(scope="session")
def published_image() -> str:
    if shutil.which("docker") is None:
        pytest.fail("The published-image checks require the Docker CLI with Docker Compose.")
    image = os.environ.get("PUBLISHED_IMAGE")
    if not image:
        pytest.fail("Set PUBLISHED_IMAGE to the published image, for example ...:sha-<commit>.")
    return image


@pytest.fixture(scope="module")
def published_stack(tmp_path_factory, published_image):
    """The Compose stack with the published image pulled from the registry, never built."""
    compose_stack = ComposeStack(tmp_path_factory.mktemp("env"), (PUBLISHED_IMAGE_FILE,))
    try:
        result = compose_stack.up(check=False, build=False)
        if result.returncode != 0:
            pytest.fail(f"docker compose up failed:\n{result.stderr}\n{compose_stack.logs()}")
        yield compose_stack
    finally:
        compose_stack.down()


@pytest.fixture(scope="module")
def image_labels(published_stack, published_image) -> dict[str, str]:
    """Labels of the pulled image (pulled by published_stack)."""
    output = subprocess.run(
        ["docker", "image", "inspect", "--format", "{{json .Config.Labels}}", published_image],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return json.loads(output)
