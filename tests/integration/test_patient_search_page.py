"""Integration tests for the patients area: search form, result list and empty state (T-09.2).

Synthetic data only. The acceptance and access tests of US-09 are T-09.3 (#40).
"""

import re
from datetime import date
from html import unescape

import pytest
from fastapi.testclient import TestClient
from markupsafe import escape

from app.db import get_session
from app.main import app
from app.models import Patient, Role, StaffAccount
from app.patients import SEARCH_LIMIT, SEARCH_MESSAGES

PASSWORD = "synthetic-password"
HTML = {"Accept": "text/html"}


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app, headers=HTML) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


def log_in(client, db_session, role: Role) -> None:
    account = StaffAccount(login=f"synthetic.{role.value}", role=role)
    account.set_password(PASSWORD)
    db_session.add(account)
    db_session.commit()
    token = re.search(r'name="csrf_token" value="([^"]+)"', client.get("/login").text).group(1)
    data = {"login": account.login, "password": PASSWORD, "csrf_token": token}
    assert client.post("/login", data=data, follow_redirects=False).status_code == 303


@pytest.fixture
def receptionist(client, db_session):
    log_in(client, db_session, Role.RECEPTIONIST)


@pytest.fixture
def patients(db_session) -> dict[str, Patient]:
    saved = {
        name: Patient(full_name=name, date_of_birth=date(1990, 5, 17))
        for name in ["Maria da Silva", "Pedro Silva", "Ana Costa"]
    }
    saved["Pedro Silva"].is_active = False
    db_session.add_all(saved.values())
    db_session.commit()
    return saved


def text_of(html: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", html)).split())


def rows(html: str) -> list[str]:
    return [text_of(row) for row in re.findall(r"<tr>\s*<td.*?</tr>", html, re.S)]


def search_input(html: str) -> str:
    return re.search(r'<input id="q"[^>]*>', html).group(0)


def test_area_shows_the_form_and_the_registration_link_without_results(client, receptionist):
    response = client.get("/patients")

    assert response.status_code == 200
    assert "<title>Patients" in response.text
    assert '<a href="/patients/new">Register a patient</a>' in response.text
    assert '<form class="search" method="get" action="/patients" role="search">' in response.text
    assert '<label for="q">Search by name or record number</label>' in response.text
    assert 'aria-describedby="q-hint"' in search_input(response.text)
    assert "<table>" not in response.text
    assert 'id="search-summary"' not in response.text
    assert "under construction" not in response.text


def test_results_list_each_patient_with_a_link_to_the_record(client, receptionist, patients):
    response = client.get("/patients", params={"q": "silva"})

    maria, pedro = patients["Maria da Silva"], patients["Pedro Silva"]
    assert response.status_code == 200
    assert '2 patients found for "silva".' in text_of(response.text)
    assert rows(response.text) == [
        f"{maria.record_number} Maria da Silva 1990-05-17 Active",
        f"{pedro.record_number} Pedro Silva 1990-05-17 Inactive",
    ]
    assert f'<a href="/patients/{maria.id}">Maria da Silva</a>' in response.text
    assert 'value="silva"' in search_input(response.text)
    # The table may scroll inside its region on small screens, so it is keyboard-reachable.
    assert (
        '<div class="results" role="region" aria-labelledby="search-summary" tabindex="0">'
        in response.text
    )


def test_a_single_result_by_record_number(client, receptionist, patients):
    ana = patients["Ana Costa"]

    response = client.get("/patients", params={"q": ana.record_number})

    assert f'1 patient found for "{ana.record_number}".' in text_of(response.text)
    assert rows(response.text) == [f"{ana.record_number} Ana Costa 1990-05-17 Active"]


def test_search_without_matches_shows_the_empty_state(client, receptionist, patients):
    response = client.get("/patients", params={"q": "nobody"})

    assert response.status_code == 200
    assert 'No patients match "nobody".' in text_of(response.text)
    assert '<a href="/patients/new">register the patient</a>' in response.text
    assert "<table>" not in response.text


@pytest.mark.parametrize(("query", "message"), [("", "empty"), ("m", "too_short")])
def test_unusable_query_shows_the_message_at_the_field(client, receptionist, query, message):
    response = client.get("/patients", params={"q": query})

    assert response.status_code == 422
    assert "<title>Error: Patients" in response.text
    message_html = escape(SEARCH_MESSAGES[message])
    assert f'<p class="field-error" id="q-error" role="alert">{message_html}</p>' in response.text
    field = search_input(response.text)
    assert 'aria-invalid="true"' in field
    assert 'aria-describedby="q-hint q-error"' in field
    assert "autofocus" in field
    assert "<table>" not in response.text


def test_more_than_the_limit_shows_a_notice(client, receptionist, db_session):
    db_session.add_all(
        Patient(full_name=f"Synthetic Limit {n:03d}", date_of_birth=date(1990, 5, 17))
        for n in range(SEARCH_LIMIT + 1)
    )
    db_session.commit()

    response = client.get("/patients", params={"q": "synthetic limit"})

    assert len(rows(response.text)) == SEARCH_LIMIT
    assert f"Only the first {SEARCH_LIMIT} patients are shown." in response.text


def test_the_query_is_escaped_in_the_page(client, receptionist):
    response = client.get("/patients", params={"q": "<b>x</b>"})

    assert "<b>x</b>" not in response.text
    assert "&lt;b&gt;x&lt;/b&gt;" in response.text


@pytest.mark.parametrize("params", [{}, {"q": "silva"}])
def test_doctors_cannot_open_the_patients_area(client, db_session, patients, params):
    log_in(client, db_session, Role.DOCTOR)

    response = client.get("/patients", params=params)

    assert response.status_code == 403
    assert "Access denied" in response.text
    assert "Silva" not in response.text
