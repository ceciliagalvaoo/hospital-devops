"""Integration tests for the staff accounts area and the account creation form (T-14.2).

Synthetic data only. The acceptance and access tests of US-14 are T-14.3 (#17).
"""

import re
from html import unescape

import pytest
from fastapi.testclient import TestClient
from markupsafe import escape
from sqlalchemy import func, select

from app.accounts import MESSAGES
from app.db import get_session
from app.main import app
from app.models import Role, StaffAccount

PASSWORD = "synthetic-password"
NEW_PASSWORD = "synthetic-new-password"
HTML = {"Accept": "text/html"}


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app, headers=HTML) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


def account(db_session, login: str, role: Role, active: bool = True) -> StaffAccount:
    staff = StaffAccount(login=login, role=role, is_active=active)
    staff.set_password(PASSWORD)
    db_session.add(staff)
    db_session.commit()
    return staff


def form_token(html: str) -> str:
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def log_in(client, db_session, role: Role) -> None:
    staff = account(db_session, f"synthetic.login.{role.value}", role)
    data = {
        "login": staff.login,
        "password": PASSWORD,
        "csrf_token": form_token(client.get("/login").text),
    }
    assert client.post("/login", data=data, follow_redirects=False).status_code == 303


@pytest.fixture
def administrator(client, db_session):
    log_in(client, db_session, Role.ADMINISTRATOR)


def submit(client, data: dict):
    token = form_token(client.get("/login").text)
    return client.post("/staff/new", data=data | {"csrf_token": token}, follow_redirects=False)


def input_tag(html: str, name: str) -> str:
    return re.search(rf'<input id="{name}"[^>]*>', html).group(0)


def rows(html: str) -> list[str]:
    return [
        " ".join(unescape(re.sub(r"<[^>]+>", " ", row)).split())
        for row in re.findall(r"<tr(?: class=\"highlight\")?>\s*<td>.*?</tr>", html, re.S)
    ]


def account_count(db_session) -> int:
    return db_session.scalar(select(func.count()).select_from(StaffAccount))


def test_area_lists_the_accounts_by_login(client, db_session, administrator):
    account(db_session, "synthetic.receptionist", Role.RECEPTIONIST)
    account(db_session, "synthetic.doctor", Role.DOCTOR, active=False)

    page = client.get("/staff").text

    assert '<a href="/staff/new">Create a staff account</a>' in page
    assert "3 accounts." in page
    assert rows(page) == [
        "synthetic.doctor Doctor Inactive",
        "synthetic.login.administrator Administrator Active",
        "synthetic.receptionist Receptionist Active",
    ]
    assert "under construction" not in page
    assert 'role="status"' not in page


def test_form_labels_the_fields_and_protects_the_passwords(client, administrator):
    page = client.get("/staff/new").text

    assert '<label for="login">Login <span class="required">(required)</span>' in page
    assert '<label for="password_confirmation">Repeat the password' in page
    assert re.findall(r'<option value="(\w+)"', page) == ["receptionist", "doctor", "administrator"]
    login, password = input_tag(page, "login"), input_tag(page, "password")
    assert 'autocomplete="off"' in login
    assert "autofocus" in login
    assert 'type="password"' in password
    assert password.count("autocomplete=") == 1
    assert 'autocomplete="new-password"' in password
    assert 'autocomplete="new-password"' in input_tag(page, "password_confirmation")


def test_creating_an_account_shows_it_in_the_list_with_a_confirmation(
    client, db_session, administrator
):
    response = submit(
        client,
        {
            "login": "Night.Shift",
            "role": "receptionist",
            "password": NEW_PASSWORD,
            "password_confirmation": NEW_PASSWORD,
        },
    )

    created = db_session.scalars(
        select(StaffAccount).where(StaffAccount.login == "night.shift")
    ).one()
    assert response.status_code == 303
    assert response.headers["location"] == f"/staff?created={created.id}"
    page = client.get(response.headers["location"]).text
    assert "Account night.shift created with the role receptionist." in page
    assert '<tr class="highlight">' in page
    assert created.check_password(NEW_PASSWORD)


def test_the_confirmation_needs_an_existing_account(client, administrator):
    assert 'role="status"' not in client.get("/staff", params={"created": 999999}).text


def test_invalid_data_keeps_login_and_role_but_never_the_passwords(
    client, db_session, administrator
):
    account(db_session, "synthetic.receptionist", Role.RECEPTIONIST)
    before = account_count(db_session)
    typed = "typed-secret-1234"

    response = submit(
        client,
        {
            "login": "Synthetic.Receptionist",
            "role": "doctor",
            "password": typed,
            "password_confirmation": typed,
        },
    )

    assert response.status_code == 422
    assert "<title>Error: Create a staff account" in response.text
    message = escape(MESSAGES["login_taken"])
    assert f'<p class="field-error" id="login-error">{message}</p>' in response.text
    assert 'value="Synthetic.Receptionist"' in input_tag(response.text, "login")
    assert '<option value="doctor" selected>' in response.text
    assert typed not in response.text
    assert 'value=""' in input_tag(response.text, "password")
    assert "autofocus" in input_tag(response.text, "login")
    assert account_count(db_session) == before


def test_different_passwords_are_identified_at_the_confirmation(client, db_session, administrator):
    response = submit(
        client,
        {
            "login": "new.account",
            "role": "doctor",
            "password": NEW_PASSWORD,
            "password_confirmation": "another-password-1",
        },
    )

    assert response.status_code == 422
    message = escape(MESSAGES["password_mismatch"])
    assert f'<a href="#password_confirmation">{message}</a>' in response.text
    assert "autofocus" in input_tag(response.text, "password_confirmation")
    assert (
        db_session.scalar(select(StaffAccount).where(StaffAccount.login == "new.account")) is None
    )


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR])
@pytest.mark.parametrize(
    ("method", "path"), [("GET", "/staff"), ("GET", "/staff/new"), ("POST", "/staff/new")]
)
def test_only_administrators_open_the_staff_pages(client, db_session, role, method, path):
    log_in(client, db_session, role)
    token = form_token(client.get("/login").text)
    before = account_count(db_session)

    response = client.request(
        method,
        path,
        data={
            "login": "new.account",
            "role": "doctor",
            "password": NEW_PASSWORD,
            "password_confirmation": NEW_PASSWORD,
            "csrf_token": token,
        },
        follow_redirects=False,
    )

    assert response.status_code == 403
    assert "Access denied" in response.text
    assert account_count(db_session) == before
