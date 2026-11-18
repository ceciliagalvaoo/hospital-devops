"""Integration tests for patient search in the database and through the API (T-09.1).

Synthetic data only. The acceptance and access tests of US-09 are T-09.3 (#40).
"""

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.access import NOT_AUTHENTICATED, NOT_PERMITTED
from app.db import get_session
from app.main import app
from app.models import Patient, Role, StaffAccount
from app.patients import SEARCH_LIMIT, SEARCH_MESSAGES, search_patients
from tests.csrf import csrf_headers

PASSWORD = "synthetic-password"
NAMES = ["Maria da Silva", "Mário Souza", "Ana Maria Costa", "Pedro Silva", "50% Synthetic_Name"]


@pytest.fixture
def patients(db_session) -> dict[str, Patient]:
    saved = {name: Patient(full_name=name, date_of_birth=date(1990, 5, 17)) for name in NAMES}
    db_session.add_all(saved.values())
    db_session.commit()
    return saved


def names(result) -> list[str]:
    return [patient.full_name for patient in result.patients]


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("maria", ["Ana Maria Costa", "Maria da Silva"]),  # ignores case, ordered by name
        ("SILVA", ["Maria da Silva", "Pedro Silva"]),
        ("silva maria", ["Maria da Silva"]),  # every word, in any order
        ("ria cos", ["Ana Maria Costa"]),  # parts of words
        ("Mário", ["Mário Souza"]),
        ("50%", ["50% Synthetic_Name"]),  # wildcards are literal
        ("ia_d", []),  # "_" would match the space of "Maria da" as a wildcard
        ("nobody", []),
    ],
)
def test_name_search(db_session, patients, query, expected):
    assert names(search_patients(db_session, query)) == expected


def test_record_number_search(db_session, patients):
    patient = patients["Pedro Silva"]

    for query in [patient.record_number, f"P{patient.id}", str(patient.id)]:
        assert names(search_patients(db_session, query)) == ["Pedro Silva"]
    assert names(search_patients(db_session, "P-999999")) == []


def test_inactive_patients_are_found(db_session, patients):
    patients["Pedro Silva"].is_active = False
    db_session.commit()

    assert names(search_patients(db_session, "pedro")) == ["Pedro Silva"]


def test_results_are_limited_and_more_is_reported(db_session):
    db_session.add_all(
        Patient(full_name=f"Synthetic Limit {n:03d}", date_of_birth=date(1990, 5, 17))
        for n in range(SEARCH_LIMIT + 1)
    )
    db_session.commit()

    result = search_patients(db_session, "synthetic limit")

    assert len(result.patients) == SEARCH_LIMIT
    assert result.more is True
    assert names(result)[0] == "Synthetic Limit 000"
    assert search_patients(db_session, "limit 000").more is False


# ---------------------------------------------------------------- API


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


def log_in(client, db_session, role: Role) -> None:
    account = StaffAccount(login=f"synthetic.{role.value}", role=role)
    account.set_password(PASSWORD)
    db_session.add(account)
    db_session.commit()
    data = {"login": account.login, "password": PASSWORD}
    assert client.post("/auth/login", data=data, headers=csrf_headers(client)).status_code == 200


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.ADMINISTRATOR])
def test_front_desk_roles_search_through_the_api(client, db_session, patients, role):
    log_in(client, db_session, role)

    response = client.get("/api/patients", params={"q": "silva"})

    assert response.status_code == 200
    assert [p["full_name"] for p in response.json()["patients"]] == [
        "Maria da Silva",
        "Pedro Silva",
    ]
    assert response.json()["patients"][1] == {
        "record_number": patients["Pedro Silva"].record_number,
        "full_name": "Pedro Silva",
        "date_of_birth": "1990-05-17",
        "phone": None,
        "email": None,
        "is_active": True,
    }
    assert response.json()["more"] is False


@pytest.mark.parametrize(("query", "message"), [("", "empty"), ("m", "too_short")])
def test_unusable_queries_return_the_message(client, db_session, query, message):
    log_in(client, db_session, Role.RECEPTIONIST)

    response = client.get("/api/patients", params={"q": query})

    assert (response.status_code, response.json()) == (
        422,
        {"detail": SEARCH_MESSAGES[message]},
    )


def test_doctors_cannot_search(client, db_session, patients):
    log_in(client, db_session, Role.DOCTOR)

    response = client.get("/api/patients", params={"q": "silva"})

    assert (response.status_code, response.json()) == (403, {"detail": NOT_PERMITTED})


def test_search_needs_a_session(client, patients):
    response = client.get("/api/patients", params={"q": "silva"})

    assert (response.status_code, response.json()) == (401, {"detail": NOT_AUTHENTICATED})
