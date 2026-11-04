import json
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = ROOT / "docker-compose.yml"
FAILING_MIGRATION_FILE = Path(__file__).with_name("compose.failing-migration.yml")
STARTUP_TIMEOUT_SECONDS = 180


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class ComposeStack:
    """An isolated Docker Compose project started from settings based on .env.example."""

    def __init__(self, env_dir: Path, extra_files: tuple[Path, ...] = ()) -> None:
        self.project = f"hospital-smoke-{uuid.uuid4().hex[:8]}"
        self.port = _free_port()
        self.env_file = env_dir / f"{self.project}.env"
        settings = (ROOT / ".env.example").read_text(encoding="utf-8")
        self.env_file.write_text(f"{settings}\nAPP_PORT={self.port}\n", encoding="utf-8")
        self.files = (COMPOSE_FILE, *extra_files)

    def compose(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        command = ["docker", "compose", "-p", self.project, "--env-file", str(self.env_file)]
        for file in self.files:
            command += ["-f", str(file)]
        return subprocess.run(
            [*command, *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=check,
            timeout=STARTUP_TIMEOUT_SECONDS + 60,
        )

    def up(self, check: bool = True) -> subprocess.CompletedProcess[str]:
        return self.compose(
            "up",
            "--detach",
            "--build",
            "--wait",
            "--wait-timeout",
            str(STARTUP_TIMEOUT_SECONDS),
            check=check,
        )

    def down(self) -> None:
        self.compose("down", "--volumes", "--rmi", "local", check=False)

    def logs(self) -> str:
        return self.compose("logs", "--no-color", check=False).stdout

    def state(self, service: str) -> dict:
        output = self.compose("ps", "--all", "--format", "json", service).stdout
        containers = [json.loads(line) for line in output.splitlines() if line.strip()]
        assert len(containers) == 1, f"expected one {service} container, found {containers}"
        return containers[0]

    def get_health(self, wait_seconds: float = 60) -> tuple[int, dict]:
        """Return the /health status and body, waiting until the application accepts connections."""
        deadline = time.monotonic() + wait_seconds
        url = f"http://127.0.0.1:{self.port}/health"
        while True:
            try:
                with urllib.request.urlopen(url, timeout=10) as response:
                    return response.status, json.loads(response.read())
            except urllib.error.HTTPError as error:
                return error.code, json.loads(error.read())
            except (urllib.error.URLError, ConnectionError):
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.5)


@pytest.fixture(scope="session", autouse=True)
def require_docker() -> None:
    if shutil.which("docker") is None:
        pytest.fail("The smoke tests require the Docker CLI with Docker Compose.")


@pytest.fixture(scope="module")
def stack(tmp_path_factory):
    compose_stack = ComposeStack(tmp_path_factory.mktemp("env"))
    try:
        result = compose_stack.up(check=False)
        if result.returncode != 0:
            pytest.fail(f"docker compose up failed:\n{result.stderr}\n{compose_stack.logs()}")
        yield compose_stack
    finally:
        compose_stack.down()


@pytest.fixture
def failing_migration_stack(tmp_path_factory):
    compose_stack = ComposeStack(tmp_path_factory.mktemp("env"), (FAILING_MIGRATION_FILE,))
    try:
        yield compose_stack
    finally:
        compose_stack.down()
