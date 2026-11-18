"""Unit tests for the patient registration rules (T-03.2). Synthetic data only."""

from datetime import date

import pytest

from app.patients import MESSAGES, InvalidPatient, PatientDetails, validate_patient

TODAY = date(2026, 11, 18)
VALID = {"full_name": "Synthetic Patient", "date_of_birth": "1990-05-17", "phone": "", "email": ""}


def validate(**fields) -> PatientDetails:
    return validate_patient(**(VALID | fields), today=TODAY)


def errors_of(**fields) -> dict[str, str]:
    with pytest.raises(InvalidPatient) as raised:
        validate(**fields)
    return raised.value.errors


def test_name_and_date_of_birth_are_enough():
    assert validate() == PatientDetails("Synthetic Patient", date(1990, 5, 17), None, None)


def test_values_are_trimmed_and_blank_contacts_are_stored_as_none():
    details = validate(
        full_name="  Synthetic Patient  ",
        date_of_birth=" 1990-05-17 ",
        phone="   ",
        email=" patient@example.test ",
    )

    assert details == PatientDetails(
        "Synthetic Patient", date(1990, 5, 17), None, "patient@example.test"
    )


@pytest.mark.parametrize("blank", ["", "   ", None])
def test_missing_name_and_date_of_birth_are_both_reported(blank):
    assert errors_of(full_name=blank, date_of_birth=blank) == {
        "full_name": MESSAGES["name_missing"],
        "date_of_birth": MESSAGES["birth_missing"],
    }


def test_name_length_limit():
    assert validate(full_name="x" * 120).full_name == "x" * 120
    assert errors_of(full_name="x" * 121) == {"full_name": MESSAGES["name_too_long"]}


@pytest.mark.parametrize("value", ["17/05/1990", "1990-02-30", "1990-13-01", "19900517", "soon"])
def test_dates_that_are_not_real_iso_dates_are_rejected(value):
    assert errors_of(date_of_birth=value) == {"date_of_birth": MESSAGES["birth_invalid"]}


def test_date_of_birth_limits():
    assert validate(date_of_birth="2026-11-18").date_of_birth == TODAY
    assert validate(date_of_birth="1900-01-01").date_of_birth == date(1900, 1, 1)
    assert errors_of(date_of_birth="2026-11-19") == {"date_of_birth": MESSAGES["birth_future"]}
    assert errors_of(date_of_birth="1899-12-31") == {"date_of_birth": MESSAGES["birth_too_early"]}


@pytest.mark.parametrize("phone", ["+55 11 91234-5678", "(11) 3456-7890", "12345678", "1" * 15])
def test_well_formed_phone_numbers_are_accepted(phone):
    assert validate(phone=phone).phone == phone


@pytest.mark.parametrize("phone", ["1234567", "1" * 16, "11 9123 abcd", "+55+11 91234-5678"])
def test_malformed_phone_numbers_are_rejected(phone):
    assert errors_of(phone=phone) == {"phone": MESSAGES["phone_invalid"]}


@pytest.mark.parametrize("email", ["patient@example.test", "first.last+tag@hospital.example"])
def test_well_formed_email_addresses_are_accepted(email):
    assert validate(email=email).email == email


@pytest.mark.parametrize(
    "email", ["patient", "patient@", "@example.test", "pa tient@example.test", "patient@example"]
)
def test_malformed_email_addresses_are_rejected(email):
    assert errors_of(email=email) == {"email": MESSAGES["email_invalid"]}


def test_email_length_limit():
    longest = "p" * 241 + "@example.test"  # 254 characters

    assert validate(email=longest).email == longest
    assert errors_of(email="p" + longest) == {"email": MESSAGES["email_invalid"]}


def test_every_invalid_field_is_reported_at_once():
    assert errors_of(full_name="", date_of_birth="2999-01-01", phone="12", email="x") == {
        "full_name": MESSAGES["name_missing"],
        "date_of_birth": MESSAGES["birth_future"],
        "phone": MESSAGES["phone_invalid"],
        "email": MESSAGES["email_invalid"],
    }
