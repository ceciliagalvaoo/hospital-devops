"""Patient registration rules (US-03), shared by the JSON API and the pages.

Only the name and the date of birth are required. The phone and e-mail are optional, but
must be well formed when given. Every invalid field is reported, so a form can mark all of
them at once.
"""

import re
from dataclasses import asdict, dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.models import Patient

NAME_MAX_LENGTH = 120  # the length of patients.full_name
EARLIEST_DATE_OF_BIRTH = date(1900, 1, 1)
ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
PHONE = re.compile(r"^\+?[0-9 ()-]+$")
PHONE_DIGITS = range(8, 16)  # 8 to 15 digits; E.164 allows at most 15
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
EMAIL_MAX_LENGTH = 254

MESSAGES = {
    "name_missing": "Enter the patient's full name.",
    "name_too_long": f"The name can have at most {NAME_MAX_LENGTH} characters.",
    "birth_missing": "Enter the date of birth.",
    "birth_invalid": "Enter a real date of birth in the form YYYY-MM-DD.",
    "birth_future": "The date of birth cannot be in the future.",
    "birth_too_early": f"The date of birth cannot be before {EARLIEST_DATE_OF_BIRTH.isoformat()}.",
    "phone_invalid": "Enter a phone number with 8 to 15 digits, for example +55 11 91234-5678.",
    "email_invalid": "Enter an e-mail address such as name@example.com.",
}


@dataclass(frozen=True)
class PatientDetails:
    full_name: str
    date_of_birth: date
    phone: str | None
    email: str | None


class InvalidPatient(ValueError):
    """The submitted patient data is invalid; ``errors`` maps each field to its message."""

    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Invalid patient data.")
        self.errors = errors


def _optional(value: str | None) -> str | None:
    value = (value or "").strip()
    return value or None


def _date_of_birth_error(value: str, today: date) -> tuple[date | None, str | None]:
    if not value:
        return None, MESSAGES["birth_missing"]
    try:
        if not ISO_DATE.match(value):
            raise ValueError(value)
        born = date.fromisoformat(value)
    except ValueError:
        return None, MESSAGES["birth_invalid"]
    if born > today:
        return None, MESSAGES["birth_future"]
    if born < EARLIEST_DATE_OF_BIRTH:
        return None, MESSAGES["birth_too_early"]
    return born, None


def validate_patient(
    full_name: str | None,
    date_of_birth: str | None,
    phone: str | None,
    email: str | None,
    *,
    today: date,
) -> PatientDetails:
    """Return the cleaned patient details, or raise InvalidPatient listing every bad field."""
    errors: dict[str, str] = {}

    name = (full_name or "").strip()
    if not name:
        errors["full_name"] = MESSAGES["name_missing"]
    elif len(name) > NAME_MAX_LENGTH:
        errors["full_name"] = MESSAGES["name_too_long"]

    born, birth_error = _date_of_birth_error((date_of_birth or "").strip(), today)
    if birth_error:
        errors["date_of_birth"] = birth_error

    phone_number = _optional(phone)
    if phone_number and not (
        PHONE.match(phone_number) and sum(c.isdigit() for c in phone_number) in PHONE_DIGITS
    ):
        errors["phone"] = MESSAGES["phone_invalid"]

    email_address = _optional(email)
    if email_address and (len(email_address) > EMAIL_MAX_LENGTH or not EMAIL.match(email_address)):
        errors["email"] = MESSAGES["email_invalid"]

    if errors:
        raise InvalidPatient(errors)
    return PatientDetails(name, born, phone_number, email_address)


def register_patient(db: Session, details: PatientDetails) -> Patient:
    """Save a new active patient and return it with its record number."""
    patient = Patient(**asdict(details))
    db.add(patient)
    db.commit()
    return patient
