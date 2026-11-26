"""Black-box end-to-end journeys against the running container (Lab 7, Task 6, #217).

The journeys use only the public HTTP interface of the application image that the CI
`Container` job built and will publish: no application code is imported and no database is
read. The development accounts are created first with the seed command, as an operator
would. Run with: pytest -m smoke
"""

import http.cookiejar
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

import pytest

pytestmark = pytest.mark.smoke

SEED_PASSWORD = "change-me-dev"  # SEED_PASSWORD of .env.example, which the stack uses
HTML = {"Accept": "text/html"}

# The RBAC matrix (docs/requirements.md §2.2), written out rather than read from the code.
AREAS = ["/patients", "/doctors", "/appointments", "/records", "/staff"]
ALLOWED = {
    "receptionist": {"/patients", "/appointments"},
    "doctor": {"/appointments", "/records"},
    "administrator": {"/patients", "/doctors", "/appointments", "/staff"},
}


@dataclass
class Reply:
    status: int
    body: str

    def json(self) -> dict:
        return json.loads(self.body)


class Browser:
    """A minimal HTTP client with a cookie jar, like a browser without JavaScript."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())
        )

    def request(self, method: str, path: str, data=None, headers=None) -> Reply:
        body = urllib.parse.urlencode(data, doseq=True).encode() if data is not None else None
        request = urllib.request.Request(
            self.base_url + path, data=body, method=method, headers=headers or {}
        )
        try:
            with self.opener.open(request, timeout=10) as response:
                return Reply(response.status, response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            return Reply(error.code, error.read().decode("utf-8"))

    def csrf(self) -> dict[str, str]:
        return {"X-CSRF-Token": self.request("GET", "/auth/csrf").json()["csrf_token"]}

    def post(self, path: str, data: dict) -> Reply:
        return self.request("POST", path, data, self.csrf())

    def log_in(self, login: str, password: str) -> Reply:
        return self.post("/auth/login", {"login": login, "password": password})


@pytest.fixture(scope="module")
def base_url(stack) -> str:
    assert stack.get_health()[0] == 200  # waits until the application accepts connections
    seeded = stack.compose("run", "--rm", "app", "python", "-m", "app.seed")
    assert seeded.returncode == 0, seeded.stderr
    return f"http://127.0.0.1:{stack.port}"


@pytest.mark.parametrize("role", ["receptionist", "doctor", "administrator"])
def test_each_role_logs_in_sees_its_areas_and_logs_out(base_url, role):
    browser = Browser(base_url)
    login = f"dev.{role}"

    assert browser.log_in(login, "wrong-password").status == 401
    assert browser.request("GET", "/auth/me").status == 401

    signed_in = browser.log_in(login, SEED_PASSWORD)
    assert signed_in.status == 200
    assert signed_in.json() == {"login": login, "role": role}
    assert browser.request("GET", "/auth/me").json() == {"login": login, "role": role}

    for area in AREAS:
        page = browser.request("GET", area, headers=HTML)
        expected = 200 if area in ALLOWED[role] else 403
        assert page.status == expected, f"{role} opening {area}"
        if expected == 403:
            assert "Access denied" in page.body

    assert browser.post("/auth/logout", {}).status == 204
    assert browser.request("GET", "/auth/me").status == 401
    for area in ALLOWED[role]:
        assert browser.request("GET", area, headers=HTML).status == 401


def test_the_front_desk_registers_and_finds_a_patient(base_url):
    receptionist = Browser(base_url)
    assert receptionist.log_in("dev.receptionist", SEED_PASSWORD).status == 200

    created = receptionist.post(
        "/api/patients",
        {"full_name": "Black Box Synthetic Patient", "date_of_birth": "1990-05-17"},
    )
    assert created.status == 201
    record_number = created.json()["record_number"]

    for query in ["black box", record_number]:
        found = receptionist.request("GET", "/api/patients?" + urllib.parse.urlencode({"q": query}))
        assert found.status == 200
        assert [p["record_number"] for p in found.json()["patients"]] == [record_number]

    doctor = Browser(base_url)
    assert doctor.log_in("dev.doctor", SEED_PASSWORD).status == 200
    assert doctor.request("GET", "/api/patients?q=black").status == 403
    refused = doctor.post("/api/patients", {"full_name": "Refused", "date_of_birth": "1990-05-17"})
    assert refused.status == 403
