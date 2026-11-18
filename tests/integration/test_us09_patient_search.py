"""Acceptance and access tests of US-09, search for a patient (T-09.3, #40).

Every case runs through both ways of searching: the JSON API (`GET /api/patients?q=`) and
the patients area page (`GET /patients?q=`). Synthetic data only.
"""

import re
from datetime import date
from html import unescape

import pytest
from fastapi.testclient import TestClient

from app.access import NOT_AUTHENTICATED, NOT_PERMITTED
from app.db import get_session
from app.main import app
from app.models import Patient, Role, StaffAccount
from app.patients import SEARCH_MESSAGES
from tests.csrf import csrf_headers

PASSWORD = "synthetic-password"
HTML = {"Accept": "text/html"}
JSON = {"Accept": "application/json"}
CHANNELS = ["api", "page"]
NAMES = ["Maria da Silva", "Ana Maria Costa", "Pedro Silva", "João Souza"]


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def patients(db_session) -> dict[str, Patient]:
    saved = {name: Patient(full_name=name, date_of_birth=date(1990, 5, 17)) for name in NAMES}
    db_session.add_all(saved.values())
    db_session.commit()
    return saved


def log_in(client, db_session, role: Role) -> StaffAccount:
    account = StaffAccount(login=f"synthetic.{role.value}", role=role)
    account.set_password(PASSWORD)
    db_session.add(account)
    db_session.commit()
    data = {"login": account.login, "password": PASSWORD}
    assert client.post("/auth/login", data=data, headers=csrf_headers(client)).status_code == 200
    return account


def search(client, channel: str, query: str):
    """Search through the API or the page; return the response, the listed record numbers
    (None when no list was shown) and the message shown instead of results."""
    if channel == "api":
        response = client.get("/api/patients", params={"q": query}, headers=JSON)
        body = response.json() if response.status_code in (200, 422) else {}
        listed = [p["record_number"] for p in body["patients"]] if "patients" in body else None
        return response, listed, body.get("detail")
    response = client.get("/patients", params={"q": query}, headers=HTML)
    rows = re.findall(r"<tr>\s*<td[^>]*>(P-\d+)</td>", response.text)
    has_list = "<table>" in response.text or "No patients match" in response.text
    error = re.search(r'id="q-error"[^>]*>(.*?)</p>', response.text)
    return response, (rows if has_list else None), unescape(error.group(1)) if error else None


def record_numbers(patients, *names) -> list[str]:
    return [patients[name].record_number for name in names]


# ---------------------------------------------------------------- criterion 1: matching patients


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.ADMINISTRATOR])
@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("maria", ["Ana Maria Costa", "Maria da Silva"]),
        ("SILVA", ["Maria da Silva", "Pedro Silva"]),
        ("silva maria", ["Maria da Silva"]),
        ("ouz", ["João Souza"]),
    ],
)
def test_search_by_name_lists_exactly_the_matching_patients(
    client, db_session, patients, role, channel, query, expected
):
    log_in(client, db_session, role)

    response, listed, message = search(client, channel, query)

    assert response.status_code == 200
    assert (listed, message) == (record_numbers(patients, *expected), None)


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize("form", ["{number}", "P{id}", "{id}", "p-{id}"])
def test_search_by_record_number_lists_that_patient(client, db_session, patients, channel, form):
    log_in(client, db_session, Role.RECEPTIONIST)
    pedro = patients["Pedro Silva"]

    _, listed, _ = search(client, channel, form.format(number=pedro.record_number, id=pedro.id))

    assert listed == [pedro.record_number]


@pytest.mark.parametrize("channel", CHANNELS)
def test_inactive_patients_are_listed_too(client, db_session, patients, channel):
    log_in(client, db_session, Role.RECEPTIONIST)
    patients["Pedro Silva"].is_active = False
    db_session.commit()

    _, listed, _ = search(client, channel, "pedro")

    assert listed == record_numbers(patients, "Pedro Silva")


@pytest.mark.parametrize("channel", CHANNELS)
def test_a_patient_registered_on_the_page_is_found_by_search(client, db_session, channel):
    # The search part of the first acceptance criterion of US-03 (#30).
    log_in(client, db_session, Role.RECEPTIONIST)
    token = client.get("/patients/new", headers=HTML).text
    token = re.search(r'name="csrf_token" value="([^"]+)"', token).group(1)
    data = {"full_name": "Synthetic Registered Patient", "date_of_birth": "1990-05-17"}
    saved = client.post("/patients/new", data=data | {"csrf_token": token}, headers=HTML)
    record_number = re.search(r'data-testid="record-number">(P-\d+)<', saved.text).group(1)

    for query in ["registered patient", record_number]:
        assert search(client, channel, query)[1] == [record_number]


# ---------------------------------------------------------------- empty and unusable queries


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize(
    ("query", "message"), [("", "empty"), ("   ", "empty"), ("m", "too_short")]
)
def test_empty_or_too_short_queries_show_a_message_instead_of_results(
    client, db_session, patients, channel, query, message
):
    log_in(client, db_session, Role.RECEPTIONIST)

    response, listed, shown = search(client, channel, query)

    assert response.status_code == 422
    assert (listed, shown) == (None, SEARCH_MESSAGES[message])


# ---------------------------------------------------------------- criterion 2: no matches


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize("query", ["nobody", "P-999999", "silva costa"])
def test_search_without_matches_shows_the_empty_state(client, db_session, patients, channel, query):
    log_in(client, db_session, Role.RECEPTIONIST)

    response, listed, message = search(client, channel, query)

    assert response.status_code == 200
    assert (listed, message) == ([], None)
    if channel == "page":
        assert f'No patients match "{query}".' in unescape(response.text)


# ---------------------------------------------------------------- criterion 3: access is refused


@pytest.mark.parametrize("channel", CHANNELS)
@pytest.mark.parametrize("query", ["silva", ""])
def test_doctors_are_refused(client, db_session, patients, channel, query):
    log_in(client, db_session, Role.DOCTOR)

    response, listed, _ = search(client, channel, query)

    assert response.status_code == 403
    assert listed is None
    assert "Silva" not in response.text
    if channel == "api":
        assert response.json() == {"detail": NOT_PERMITTED}
    else:
        assert "Access denied" in response.text


@pytest.mark.parametrize("channel", CHANNELS)
def test_search_without_a_session_is_refused(client, patients, channel):
    response, listed, _ = search(client, channel, "silva")

    assert response.status_code == 401
    assert listed is None
    if channel == "api":
        assert response.json() == {"detail": NOT_AUTHENTICATED}
    else:
        assert "Please log in to continue." in response.text


def test_a_deactivated_account_can_no_longer_search(client, db_session, patients):
    account = log_in(client, db_session, Role.RECEPTIONIST)
    account.is_active = False
    db_session.commit()

    response, listed, _ = search(client, "api", "silva")

    assert (response.status_code, listed) == (401, None)
