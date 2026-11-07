"""An isolated Docker Compose project for the container checks (smoke and published image)."""

import json
import socket
import subprocess
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPOSE_FILE = ROOT / "docker-compose.yml"
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

    def up(self, check: bool = True, build: bool = True) -> subprocess.CompletedProcess[str]:
        """Start the stack; with build=False, images are pulled instead of built locally."""
        image_source = ("--build",) if build else ("--no-build", "--pull", "always")
        return self.compose(
            "up",
            "--detach",
            *image_source,
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

    def get(self, path: str, wait_seconds: float = 60) -> tuple[int, str]:
        """Return the status and body of a GET request, waiting until the application accepts
        connections."""
        deadline = time.monotonic() + wait_seconds
        url = f"http://127.0.0.1:{self.port}{path}"
        while True:
            try:
                with urllib.request.urlopen(url, timeout=10) as response:
                    return response.status, response.read().decode("utf-8")
            except urllib.error.HTTPError as error:
                return error.code, error.read().decode("utf-8")
            except (urllib.error.URLError, ConnectionError):
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.5)

    def get_health(self, wait_seconds: float = 60) -> tuple[int, dict]:
        """Return the /health status and body."""
        status, body = self.get("/health", wait_seconds)
        return status, json.loads(body)
