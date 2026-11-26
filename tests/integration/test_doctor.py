"""Integration tests for the doctor and availability models and their migration (T-02.1).

Synthetic data only.
"""

from datetime import time

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.models import AvailabilityRange, Doctor, Role, Specialisation, StaffAccount, Weekday


@pytest.fixture
def doctor_account(db_session) -> StaffAccount:
    account = StaffAccount(login="synthetic.doctor", role=Role.DOCTOR)
    account.set_password("synthetic-password")
    db_session.add(account)
    db_session.commit()
    return account


def make_doctor(account: StaffAccount, **fields) -> Doctor:
    values = {
        "account": account,
        "full_name": "Dr Synthetic Doctor",
        "specialisation": Specialisation.CARDIOLOGY,
    }
    return Doctor(**(values | fields))


def test_doctor_is_saved_active_and_linked_to_its_account(db_session, doctor_account):
    db_session.add(make_doctor(doctor_account))
    db_session.commit()

    saved = db_session.scalars(select(Doctor)).one()
    assert saved.account.login == "synthetic.doctor"
    assert saved.specialisation is Specialisation.CARDIOLOGY
    assert saved.is_active is True
    assert saved.created_at is not None
    assert saved.availability == []


def test_availability_is_saved_and_ordered_by_weekday_and_time(db_session, doctor_account):
    doctor = make_doctor(doctor_account)
    doctor.availability = [
        AvailabilityRange(weekday=Weekday.WEDNESDAY, start_time=time(14), end_time=time(18)),
        AvailabilityRange(weekday=Weekday.MONDAY, start_time=time(14), end_time=time(17)),
        AvailabilityRange(weekday=Weekday.MONDAY, start_time=time(8), end_time=time(12)),
    ]
    db_session.add(doctor)
    db_session.commit()
    db_session.expire_all()

    saved = db_session.scalars(select(Doctor)).one()
    assert [(r.weekday, r.start_time, r.end_time) for r in saved.availability] == [
        (Weekday.MONDAY, time(8), time(12)),
        (Weekday.MONDAY, time(14), time(17)),
        (Weekday.WEDNESDAY, time(14), time(18)),
    ]


def test_an_account_has_at_most_one_doctor_profile(db_session, doctor_account):
    db_session.add(make_doctor(doctor_account))
    db_session.commit()
    db_session.add(make_doctor(doctor_account, full_name="Dr Second Profile"))

    with pytest.raises(IntegrityError, match="uq_doctors_staff_account_id"):
        db_session.commit()


def test_unsupported_specialisation_is_rejected_by_the_database(db_session, doctor_account):
    with pytest.raises(IntegrityError, match="ck_doctors_specialisation"):
        db_session.execute(
            text(
                "INSERT INTO doctors (staff_account_id, full_name, specialisation) "
                "VALUES (:account, 'Dr Synthetic', 'astrology')"
            ),
            {"account": doctor_account.id},
        )


@pytest.mark.parametrize("name", ["", "   "])
def test_blank_name_is_rejected_by_the_database(db_session, doctor_account, name):
    with pytest.raises(IntegrityError, match="ck_doctors_full_name_not_blank"):
        db_session.execute(
            text(
                "INSERT INTO doctors (staff_account_id, full_name, specialisation) "
                "VALUES (:account, :name, 'cardiology')"
            ),
            {"account": doctor_account.id, "name": name},
        )


@pytest.mark.parametrize(
    ("weekday", "start", "end", "constraint"),
    [
        (7, "08:00", "12:00", "ck_doctor_availability_weekday_range"),
        (-1, "08:00", "12:00", "ck_doctor_availability_weekday_range"),
        (0, "12:00", "12:00", "ck_doctor_availability_end_after_start"),
        (0, "12:00", "08:00", "ck_doctor_availability_end_after_start"),
    ],
)
def test_malformed_ranges_are_rejected_by_the_database(
    db_session, doctor_account, weekday, start, end, constraint
):
    doctor = make_doctor(doctor_account)
    db_session.add(doctor)
    db_session.commit()

    with pytest.raises(IntegrityError, match=constraint):
        db_session.execute(
            text(
                "INSERT INTO doctor_availability (doctor_id, weekday, start_time, end_time) "
                "VALUES (:doctor, :weekday, :start, :end)"
            ),
            {"doctor": doctor.id, "weekday": weekday, "start": start, "end": end},
        )


def test_removing_a_range_from_the_profile_deletes_it(db_session, doctor_account):
    doctor = make_doctor(doctor_account)
    doctor.availability = [
        AvailabilityRange(weekday=Weekday.MONDAY, start_time=time(8), end_time=time(12)),
        AvailabilityRange(weekday=Weekday.TUESDAY, start_time=time(8), end_time=time(12)),
    ]
    db_session.add(doctor)
    db_session.commit()

    doctor.availability = doctor.availability[1:]  # how US-13 will replace the ranges
    db_session.commit()

    remaining = db_session.scalars(select(AvailabilityRange)).all()
    assert [r.weekday for r in remaining] == [Weekday.TUESDAY]


def test_deleting_a_profile_deletes_its_availability(db_session, doctor_account):
    doctor = make_doctor(doctor_account)
    doctor.availability = [
        AvailabilityRange(weekday=Weekday.MONDAY, start_time=time(8), end_time=time(12))
    ]
    db_session.add(doctor)
    db_session.commit()

    db_session.execute(text("DELETE FROM doctors"))

    assert db_session.scalar(text("SELECT count(*) FROM doctor_availability")) == 0


def test_an_account_with_a_doctor_profile_cannot_be_deleted(db_session, doctor_account):
    db_session.add(make_doctor(doctor_account))
    db_session.commit()

    with pytest.raises(IntegrityError, match="fk_doctors_staff_account_id_staff_accounts"):
        db_session.execute(text("DELETE FROM staff_accounts"))


def test_labels_for_the_pages():
    assert Specialisation.GENERAL_PRACTICE.label == "General practice"
    assert [s.label for s in Specialisation][1:3] == ["Cardiology", "Dermatology"]
    assert Weekday.MONDAY.label == "Monday"
    assert Weekday(6).label == "Sunday"
