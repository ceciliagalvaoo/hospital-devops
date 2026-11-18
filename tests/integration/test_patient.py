"""Integration tests for the patient model and its migration (T-03.1). Synthetic data only."""

from datetime import date

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.models import Patient


def make_patient(**fields) -> Patient:
    values = {"full_name": "Synthetic Patient", "date_of_birth": date(1990, 5, 17)}
    return Patient(**(values | fields))


def test_patient_is_saved_with_only_the_required_fields(db_session):
    db_session.add(make_patient())
    db_session.commit()

    saved = db_session.scalars(select(Patient)).one()
    assert (saved.full_name, saved.date_of_birth) == ("Synthetic Patient", date(1990, 5, 17))
    assert saved.phone is None
    assert saved.email is None
    assert saved.is_active is True
    assert saved.created_at is not None


def test_contact_details_and_inactive_status_are_stored(db_session):
    db_session.add(
        make_patient(phone="+55 11 90000-0000", email="patient@example.test", is_active=False)
    )
    db_session.commit()

    saved = db_session.scalars(select(Patient)).one()
    assert (saved.phone, saved.email, saved.is_active) == (
        "+55 11 90000-0000",
        "patient@example.test",
        False,
    )


def test_record_number_is_derived_from_the_id():
    assert Patient(id=42).record_number == "P-000042"
    assert Patient(id=1234567).record_number == "P-1234567"


def test_each_patient_gets_a_different_record_number(db_session):
    first, second = make_patient(), make_patient(full_name="Another Synthetic Patient")
    db_session.add_all([first, second])
    db_session.commit()

    assert first.record_number != second.record_number


@pytest.mark.parametrize("column", ["full_name", "date_of_birth"])
def test_name_and_date_of_birth_are_required_by_the_database(db_session, column):
    with pytest.raises(IntegrityError, match=f'null value in column "{column}"'):
        db_session.add(make_patient(**{column: None}))
        db_session.commit()


@pytest.mark.parametrize("name", ["", "   "])
def test_blank_name_is_rejected_by_the_database(db_session, name):
    with pytest.raises(IntegrityError, match="ck_patients_full_name_not_blank"):
        db_session.execute(
            text("INSERT INTO patients (full_name, date_of_birth) VALUES (:name, '1990-05-17')"),
            {"name": name},
        )
