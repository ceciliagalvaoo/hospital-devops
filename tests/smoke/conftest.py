import os
import shutil
from pathlib import Path

import pytest

from tests.compose_stack import ComposeStack

FAILING_MIGRATION_FILE = Path(__file__).with_name("compose.failing-migration.yml")
LOCAL_IMAGE_FILE = Path(__file__).with_name("compose.local-image.yml")


def image_setup() -> tuple[tuple[Path, ...], str]:
    """With SMOKE_IMAGE set (in CI), use that already built image; otherwise build it."""
    if os.environ.get("SMOKE_IMAGE"):
        return (LOCAL_IMAGE_FILE,), "local"
    return (), "build"


@pytest.fixture(scope="session", autouse=True)
def require_docker() -> None:
    if shutil.which("docker") is None:
        pytest.fail("The smoke tests require the Docker CLI with Docker Compose.")


@pytest.fixture(scope="module")
def stack(tmp_path_factory):
    extra_files, source = image_setup()
    compose_stack = ComposeStack(tmp_path_factory.mktemp("env"), extra_files, source)
    try:
        result = compose_stack.up(check=False)
        if result.returncode != 0:
            pytest.fail(f"docker compose up failed:\n{result.stderr}\n{compose_stack.logs()}")
        yield compose_stack
    finally:
        compose_stack.down()


@pytest.fixture
def failing_migration_stack(tmp_path_factory):
    extra_files, source = image_setup()
    compose_stack = ComposeStack(
        tmp_path_factory.mktemp("env"), (*extra_files, FAILING_MIGRATION_FILE), source
    )
    try:
        yield compose_stack
    finally:
        compose_stack.down()
