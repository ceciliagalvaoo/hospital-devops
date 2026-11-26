"""Integration tests for the doctors area, the registration form and the profile (T-02.3).

Synthetic data only. The acceptance and access tests of US-02 are T-02.4 (#58).
"""

import re
from datetime import time
from html import unescape

import pytest
from fastapi.testclient import TestClient
from markupsafe import escape
from sqlalchemy import func, select

from app.db import get_session
from app.doctors import MESSAGES
from app.main import app
from app.models import AvailabilityRange, Doctor, Role, Specialisation, StaffAccount, Weekday

PASSWORD = "synthetic-password"
HTML = {"Accept": "text/html"}


@pytest.fixture
def client(db_session):
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app, headers=HTML) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_session, None)


def account(db_session, login: str, role: Role = Role.DOCTOR) -> StaffAccount:
    staff = StaffAccount(login=login, role=role)
    staff.set_password(PASSWORD)
    db_session.add(staff)
    db_session.commit()
    return staff


def form_token(html: str) -> str:
    return re.search(r'name="csrf_token" value="([^"]+)"', html).group(1)


def log_in(client, db_session, role: Role) -> None:
    staff = account(db_session, f"synthetic.login.{role.value}", role)
    token = form_token(client.get("/login").text)
    data = {"login": staff.login, "password": PASSWORD, "csrf_token": token}
    assert client.post("/login", data=data, follow_redirects=False).status_code == 303


@pytest.fixture
def administrator(client, db_session):
    log_in(client, db_session, Role.ADMINISTRATOR)


def submit(client, data: dict):
    token = form_token(client.get("/login").text)
    return client.post("/doctors/new", data=data | {"csrf_token": token}, follow_redirects=False)


def valid_form(staff: StaffAccount, **fields) -> dict:
    return {
        "staff_account_id": str(staff.id),
        "full_name": "Dr Synthetic Doctor",
        "specialisation": "cardiology",
        "weekday": ["2", "0", ""],
        "start_time": ["14:00", "08:00", ""],
        "end_time": ["18:00", "12:00", ""],
    } | fields


def text_of(html: str) -> str:
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", html)).split())


def tag(html: str, element: str, element_id: str) -> str:
    return re.search(rf'<{element} id="{element_id}"[^>]*>', html).group(0)


def options(html: str, select_id: str) -> list[str]:
    block = re.search(rf'<select id="{select_id}".*?</select>', html, re.S).group(0)
    return [unescape(text) for text in re.findall(r"<option[^>]*>([^<]*)</option>", block)]


def selected(html: str, select_id: str) -> str | None:
    block = re.search(rf'<select id="{select_id}".*?</select>', html, re.S).group(0)
    found = re.search(r'<option value="([^"]*)" selected>', block)
    return found.group(1) if found else None


def doctor_count(db_session) -> int:
    return db_session.scalar(select(func.count()).select_from(Doctor))


# ---------------------------------------------------------------- doctors area


def test_area_without_doctors_shows_the_link_and_an_empty_state(client, administrator):
    response = client.get("/doctors")

    assert response.status_code == 200
    assert '<a href="/doctors/new">Register a doctor</a>' in response.text
    assert "No doctors are registered yet." in response.text
    assert "under construction" not in response.text


def test_area_lists_the_doctors_by_name(client, db_session, administrator):
    for login, name, speciality in [
        ("synthetic.doctor.b", "Dr Bruno Synthetic", Specialisation.NEUROLOGY),
        ("synthetic.doctor.a", "Dr Ana Synthetic", Specialisation.GENERAL_PRACTICE),
    ]:
        db_session.add(
            Doctor(account=account(db_session, login), full_name=name, specialisation=speciality)
        )
    db_session.commit()
    ana, bruno = db_session.scalars(select(Doctor).order_by(Doctor.full_name)).all()

    page = client.get("/doctors").text

    assert "2 doctors registered." in page
    rows = [text_of(row) for row in re.findall(r"<tr>\s*<td>.*?</tr>", page, re.S)]
    assert rows == [
        "Dr Ana Synthetic General practice synthetic.doctor.a Active",
        "Dr Bruno Synthetic Neurology synthetic.doctor.b Active",
    ]
    # Each name links to its own profile, not only the first one.
    assert f'<a href="/doctors/{ana.id}">Dr Ana Synthetic</a>' in page
    assert f'<a href="/doctors/{bruno.id}">Dr Bruno Synthetic</a>' in page


# ---------------------------------------------------------------- registration form


def test_form_offers_only_eligible_accounts_and_the_specialisation_list(
    client, db_session, administrator
):
    account(db_session, "synthetic.doctor.free")
    taken = account(db_session, "synthetic.doctor.taken")
    db_session.add(
        Doctor(account=taken, full_name="Dr Taken", specialisation=Specialisation.CARDIOLOGY)
    )
    db_session.commit()

    page = client.get("/doctors/new").text

    assert options(page, "staff_account_id") == [
        "Choose a doctor account…",
        "synthetic.doctor.free",
    ]
    assert options(page, "specialisation")[1:] == [s.label for s in Specialisation]
    assert (
        '<label for="staff_account_id">Staff account <span class="required">(required)</span>'
        in page
    )
    assert 'aria-required="true"' in tag(page, "select", "specialisation")
    assert "autofocus" in tag(page, "select", "staff_account_id")
    assert "Every active doctor account already has a doctor profile." not in page


def test_form_has_six_labelled_availability_rows(client, administrator):
    page = client.get("/doctors/new").text

    assert page.count('<fieldset class="range">') == 6
    for row in range(1, 7):
        assert f"<legend>Range {row}</legend>" in page
        assert f'<label for="availability_{row}">Weekday</label>' in page
        assert f'<label for="start_time_{row}">Start</label>' in page
        assert 'step="1800"' in tag(page, "input", f"end_time_{row}")
    assert options(page, "availability_1")[1:] == [d.label for d in Weekday]


def test_form_says_when_no_account_is_eligible(client, administrator):
    page = client.get("/doctors/new").text

    assert "Every active doctor account already has a doctor profile." in page


def test_registration_shows_the_profile_with_a_confirmation(client, db_session, administrator):
    staff = account(db_session, "synthetic.doctor")

    response = submit(client, valid_form(staff))

    doctor = db_session.scalars(select(Doctor)).one()
    assert response.status_code == 303
    assert response.headers["location"] == f"/doctors/{doctor.id}?registered=1"
    page = text_of(client.get(response.headers["location"]).text)
    assert "Doctor registered and linked to the account synthetic.doctor." in page
    assert "Specialisation Cardiology Staff account synthetic.doctor Status Active" in page
    assert "Monday 08:00 12:00 Wednesday 14:00 18:00" in page  # ordered by day and time
    assert [(r.weekday, r.start_time) for r in doctor.availability] == [
        (Weekday.MONDAY, time(8)),
        (Weekday.WEDNESDAY, time(14)),
    ]


def test_profile_without_the_confirmation(client, db_session, administrator):
    staff = account(db_session, "synthetic.doctor")
    doctor = Doctor(
        account=staff, full_name="Dr Synthetic", specialisation=Specialisation.PSYCHIATRY
    )
    doctor.availability = [
        AvailabilityRange(weekday=Weekday.FRIDAY, start_time=time(9), end_time=time(13, 30))
    ]
    db_session.add(doctor)
    db_session.commit()

    page = text_of(client.get(f"/doctors/{doctor.id}").text)

    assert "Doctor registered" not in page
    assert "Friday 09:00 13:30" in page


def test_invalid_data_keeps_the_values_and_identifies_every_field_and_row(
    client, db_session, administrator
):
    staff = account(db_session, "synthetic.doctor")
    data = valid_form(
        staff,
        specialisation="",
        weekday=["0", "0", "2"],
        start_time=["08:00", "11:00", "14:15"],
        end_time=["12:00", "13:00", "18:00"],
    )

    response = submit(client, data)

    assert response.status_code == 422
    assert "<title>Error: Register a doctor" in response.text
    summary = re.search(r'<div class="message error" role="alert".*?</div>', response.text, re.S)
    assert [unescape(t) for t in re.findall(r'<a href="#([^"]+)">', summary.group(0))] == [
        "specialisation",
        "availability_2",
        "availability_3",
    ]
    overlap = escape(MESSAGES["range_overlap"])
    assert f'<p class="field-error" id="availability_2-error">{overlap}</p>' in response.text
    assert 'aria-invalid="true"' in tag(response.text, "input", "start_time_2")
    assert 'aria-describedby="availability_2-error"' in tag(
        response.text, "select", "availability_2"
    )
    assert "aria-invalid" not in tag(response.text, "input", "start_time_1")
    assert "autofocus" in tag(response.text, "select", "specialisation")
    assert selected(response.text, "staff_account_id") == str(staff.id)
    assert 'value="Dr Synthetic Doctor"' in tag(response.text, "input", "full_name")
    assert selected(response.text, "availability_3") == "2"
    assert 'value="14:15"' in tag(response.text, "input", "start_time_3")
    assert response.text.count('<fieldset class="range') == 6
    assert doctor_count(db_session) == 0


def test_no_range_shows_the_message_at_the_availability(client, db_session, administrator):
    staff = account(db_session, "synthetic.doctor")

    response = submit(client, valid_form(staff, weekday=[], start_time=[], end_time=[]))

    assert response.status_code == 422
    message = escape(MESSAGES["availability_missing"])
    assert f'<p class="field-error" id="availability-error">{message}</p>' in response.text
    assert "autofocus" in tag(response.text, "select", "availability_1")


@pytest.mark.parametrize("path", ["/doctors/999999", "/doctors/abc"])
def test_unknown_doctor_profiles_are_not_found(client, administrator, path):
    response = client.get(path)

    assert response.status_code == 404
    assert "Page not found" in response.text


@pytest.mark.parametrize("role", [Role.RECEPTIONIST, Role.DOCTOR])
@pytest.mark.parametrize(
    ("method", "path"),
    [("GET", "/doctors"), ("GET", "/doctors/new"), ("POST", "/doctors/new"), ("GET", "/doctors/1")],
)
def test_only_administrators_open_the_doctor_pages(client, db_session, role, method, path):
    log_in(client, db_session, role)
    token = form_token(client.get("/login").text)

    response = client.request(method, path, data={"csrf_token": token}, follow_redirects=False)

    assert response.status_code == 403
    assert "Access denied" in response.text
