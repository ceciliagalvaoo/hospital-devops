"""Integration tests for the staff accounts area and the account creation form (T-14.2).

Synthetic data only. The acceptance and access tests of US-14 are T-14.3 (#17), those of US-15
T-15.3 (#22).
"""

import re
from html import unescape

import pytest
from fastapi.testclient import TestClient
from markupsafe import escape
from sqlalchemy import func, select

from app.accounts import MESSAGES, OWN_ACCOUNT
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
        "synthetic.doctor Doctor Inactive —",
        "synthetic.login.administrator Administrator Active Your account",
        "synthetic.receptionist Receptionist Active Deactivate",
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
    ("method", "path"),
    [
        ("GET", "/staff"),
        ("GET", "/staff/new"),
        ("POST", "/staff/new"),
        ("GET", "/staff/1/deactivate"),
        ("POST", "/staff/1/deactivate"),
    ],
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


# ---------------------------------------------------------------- deactivation (T-15.2)


def own_account(db_session) -> StaffAccount:
    return db_session.scalar(
        select(StaffAccount).where(StaffAccount.login == "synthetic.login.administrator")
    )


def deactivate(client, account_id: int):
    token = form_token(client.get("/login").text)
    return client.post(
        f"/staff/{account_id}/deactivate", data={"csrf_token": token}, follow_redirects=False
    )


def is_active(db_session, staff: StaffAccount) -> bool:
    db_session.expire_all()
    return staff.is_active


def test_the_list_links_each_other_active_account_to_its_deactivation(
    client, db_session, administrator
):
    target = account(db_session, "synthetic.receptionist", Role.RECEPTIONIST)
    inactive = account(db_session, "synthetic.doctor", Role.DOCTOR, active=False)

    page = client.get("/staff").text

    assert (
        f'<a href="/staff/{target.id}/deactivate" aria-label="Deactivate synthetic.receptionist">'
        "Deactivate</a>" in page
    )
    assert f"/staff/{inactive.id}/deactivate" not in page
    assert f"/staff/{own_account(db_session).id}/deactivate" not in page


def test_the_confirmation_explains_the_effect_and_changes_nothing(
    client, db_session, administrator
):
    target = account(db_session, "synthetic.receptionist", Role.RECEPTIONIST)

    response = client.get(f"/staff/{target.id}/deactivate")

    page = " ".join(unescape(re.sub(r"<[^>]+>", " ", response.text)).split())
    assert response.status_code == 200
    assert "<title>Deactivate synthetic.receptionist" in response.text
    assert (
        "<p>Deactivate the receptionist account <strong>synthetic.receptionist</strong>?</p>"
        in response.text
    )
    assert "It can no longer log in." in page
    assert "Anyone using it now is logged out at once." in page
    assert "The account and the records that refer to it are kept." in page
    assert f'<form method="post" action="/staff/{target.id}/deactivate">' in response.text
    assert '<button type="submit" autofocus>Deactivate account</button>' in response.text
    assert '<a href="/staff">Cancel</a>' in response.text
    assert is_active(db_session, target)  # opening the confirmation deactivates nothing


def test_confirming_deactivates_and_shows_the_list_with_a_confirmation(
    client, db_session, administrator
):
    target = account(db_session, "synthetic.receptionist", Role.RECEPTIONIST)

    response = deactivate(client, target.id)

    assert response.status_code == 303
    assert response.headers["location"] == f"/staff?deactivated={target.id}"
    assert not is_active(db_session, target)
    page = client.get(response.headers["location"]).text
    assert (
        '<p class="message notice" role="status">Account synthetic.receptionist deactivated. '
        "It can no longer log in.</p>" in page
    )
    assert re.search(r'<tr class="highlight">\s*<td>synthetic.receptionist</td>', page)
    assert "synthetic.receptionist Receptionist Inactive —" in rows(page)


def test_an_inactive_account_is_explained_without_a_button(client, db_session, administrator):
    inactive = account(db_session, "synthetic.doctor", Role.DOCTOR, active=False)

    response = client.get(f"/staff/{inactive.id}/deactivate")

    assert response.status_code == 200
    assert "The account synthetic.doctor is already inactive." in response.text
    assert "Deactivate account</button>" not in response.text


def test_the_own_account_cannot_be_deactivated(client, db_session, administrator):
    own = own_account(db_session)

    shown = client.get(f"/staff/{own.id}/deactivate")
    submitted = deactivate(client, own.id)

    for response in (shown, submitted):
        assert response.status_code == 409
        assert "<title>Error: Deactivate synthetic.login.administrator" in response.text
        assert escape(OWN_ACCOUNT) in response.text
        assert "Deactivate account</button>" not in response.text
    assert is_active(db_session, own)
    assert client.get("/staff").status_code == 200  # still logged in


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("path", ["/staff/999999/deactivate", "/staff/abc/deactivate"])
def test_unknown_accounts_cannot_be_deactivated(client, administrator, method, path):
    token = form_token(client.get("/login").text)

    response = client.request(method, path, data={"csrf_token": token})

    assert response.status_code == 404
