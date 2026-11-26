"""Doctor registration rules (US-02), shared by the JSON API and the pages.

A doctor profile belongs to an active staff account with the doctor role that has no profile
yet. The name and the specialisation are required, and the availability is at least one
weekly range on the half hour, ranges of the same day not overlapping. Every invalid field
is reported at once; an invalid range is reported by its row (``availability_1`` is the
first row), so that a form can mark the row.
"""

import re
from dataclasses import dataclass, field
from datetime import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AvailabilityRange, Doctor, Role, Specialisation, StaffAccount, Weekday

NAME_MAX_LENGTH = 120  # the length of doctors.full_name
HALF_HOUR = re.compile(r"^([01]\d|2[0-3]):(00|30)$")

MESSAGES = {
    "account_missing": "Choose the doctor's staff account.",
    "account_unavailable": (
        "Choose an active staff account with the doctor role that has no doctor profile yet."
    ),
    "name_missing": "Enter the doctor's full name.",
    "name_too_long": f"The name can have at most {NAME_MAX_LENGTH} characters.",
    "specialisation_invalid": "Choose a specialisation from the list.",
    "availability_missing": "Add at least one weekly availability range.",
    "range_incomplete": "Choose the weekday and enter the start and end of this range.",
    "range_weekday": "Choose a weekday from the list.",
    "range_time": "Enter the times on the half hour, as HH:MM, for example 08:00 or 13:30.",
    "range_order": "The end of this range must be after its start.",
    "range_overlap": "This range overlaps another range on the same day.",
}


@dataclass(frozen=True)
class WeeklyRange:
    weekday: Weekday
    start: time
    end: time


@dataclass(frozen=True)
class DoctorDetails:
    staff_account_id: int
    full_name: str
    specialisation: Specialisation
    availability: list[WeeklyRange] = field(default_factory=list)


class InvalidDoctor(ValueError):
    """The submitted doctor data is invalid; ``errors`` maps each field to its message."""

    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Invalid doctor data.")
        self.errors = errors


def _range(weekday: str, start: str, end: str) -> tuple[WeeklyRange | None, str | None]:
    """Read one row of the availability; return the range or the key of its error."""
    if not (weekday and start and end):
        return None, "range_incomplete"
    if not weekday.isdigit() or int(weekday) not in iter(Weekday):
        return None, "range_weekday"
    if not (HALF_HOUR.match(start) and HALF_HOUR.match(end)):
        return None, "range_time"
    begins, ends = time.fromisoformat(start), time.fromisoformat(end)
    if ends <= begins:
        return None, "range_order"
    return WeeklyRange(Weekday(int(weekday)), begins, ends), None


def _row_number(key: str) -> int:
    """1 for ``availability_1``; 0 for the general ``availability`` key."""
    number = key.rpartition("_")[2]
    return int(number) if number.isdigit() else 0


def validate_availability(
    weekdays: list[str], starts: list[str], ends: list[str]
) -> tuple[list[WeeklyRange], dict[str, str]]:
    """Read the rows of the availability form; rows left completely empty are ignored."""
    errors: dict[str, str] = {}
    ranges: list[tuple[int, WeeklyRange]] = []
    rows = max(len(weekdays), len(starts), len(ends))
    for number in range(1, rows + 1):
        values = [
            (column[number - 1] if number <= len(column) else "").strip()
            for column in (weekdays, starts, ends)
        ]
        if not any(values):
            continue
        weekly, error = _range(*values)
        if error:
            errors[f"availability_{number}"] = MESSAGES[error]
        else:
            ranges.append((number, weekly))
    for number, weekly in ranges:
        if any(
            other.weekday == weekly.weekday
            and other.start < weekly.end
            and weekly.start < other.end
            for earlier, other in ranges
            if earlier < number
        ):
            errors[f"availability_{number}"] = MESSAGES["range_overlap"]
    if not ranges and not errors:
        errors["availability"] = MESSAGES["availability_missing"]
    # Overlaps are found in a second pass; report every row in form order.
    ordered = dict(sorted(errors.items(), key=lambda item: _row_number(item[0])))
    return [weekly for _, weekly in ranges], ordered


def eligible_accounts(db: Session) -> list[StaffAccount]:
    """Active doctor accounts without a doctor profile, which a profile may be created for."""
    with_profile = select(Doctor.staff_account_id)
    return list(
        db.scalars(
            select(StaffAccount)
            .where(
                StaffAccount.role == Role.DOCTOR,
                StaffAccount.is_active,
                StaffAccount.id.not_in(with_profile),
            )
            .order_by(StaffAccount.login)
        )
    )


def validate_doctor(
    db: Session,
    staff_account_id: str | None,
    full_name: str | None,
    specialisation: str | None,
    weekdays: list[str],
    starts: list[str],
    ends: list[str],
) -> DoctorDetails:
    """Return the cleaned doctor details, or raise InvalidDoctor listing every bad field."""
    errors: dict[str, str] = {}

    account_id = (staff_account_id or "").strip()
    if not account_id:
        errors["staff_account_id"] = MESSAGES["account_missing"]
    elif not account_id.isdigit() or int(account_id) not in {
        account.id for account in eligible_accounts(db)
    }:
        errors["staff_account_id"] = MESSAGES["account_unavailable"]

    name = (full_name or "").strip()
    if not name:
        errors["full_name"] = MESSAGES["name_missing"]
    elif len(name) > NAME_MAX_LENGTH:
        errors["full_name"] = MESSAGES["name_too_long"]

    chosen = (specialisation or "").strip()
    if chosen not in {item.value for item in Specialisation}:
        errors["specialisation"] = MESSAGES["specialisation_invalid"]

    availability, availability_errors = validate_availability(weekdays, starts, ends)
    errors |= availability_errors

    if errors:
        raise InvalidDoctor(errors)
    return DoctorDetails(int(account_id), name, Specialisation(chosen), availability)


def register_doctor(db: Session, details: DoctorDetails) -> Doctor:
    """Save a new active doctor profile with its weekly availability."""
    doctor = Doctor(
        staff_account_id=details.staff_account_id,
        full_name=details.full_name,
        specialisation=details.specialisation,
        availability=[
            AvailabilityRange(weekday=r.weekday, start_time=r.start, end_time=r.end)
            for r in details.availability
        ],
    )
    db.add(doctor)
    db.commit()
    return doctor
