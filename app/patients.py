"""Patient registration (US-03) and search (US-09) rules, shared by the JSON API and the pages.

Only the name and the date of birth are required. The phone and e-mail are optional, but
must be well formed when given. Every invalid field is reported, so a form can mark all of
them at once.
"""

import re
from dataclasses import asdict, dataclass
from datetime import date

from sqlalchemy import func, select
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


# ---------------------------------------------------------------- search (US-09)

SEARCH_LIMIT = 50
NAME_SEARCH_MIN_LENGTH = 2
RECORD_NUMBER = re.compile(r"^(?:P-?)?0*(\d+)$", re.IGNORECASE)
SEARCH_MESSAGES = {
    "empty": "Enter a name or a record number to search.",
    "too_short": f"Enter at least {NAME_SEARCH_MIN_LENGTH} characters of the name.",
}


class InvalidSearch(ValueError):
    """The search query cannot be used; ``message`` says what to enter instead."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


@dataclass(frozen=True)
class SearchQuery:
    record_id: int | None  # set when the query is a record number such as P-000042
    words: tuple[str, ...]  # otherwise the words that every matching name contains


@dataclass(frozen=True)
class SearchResult:
    patients: list[Patient]
    more: bool  # True when more than SEARCH_LIMIT patients match


def parse_search(query: str | None) -> SearchQuery:
    """Read a query as a record number (P-000042, P42 or 42) or as words of the name."""
    text = " ".join((query or "").split())
    if not text:
        raise InvalidSearch(SEARCH_MESSAGES["empty"])
    record = RECORD_NUMBER.match(text)
    if record:
        return SearchQuery(int(record.group(1)), ())
    if len(text) < NAME_SEARCH_MIN_LENGTH:
        raise InvalidSearch(SEARCH_MESSAGES["too_short"])
    return SearchQuery(None, tuple(text.split(" ")))


def _contains(word: str) -> str:
    """A LIKE pattern that matches the word literally, with % and _ escaped."""
    escaped = word.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def search_patients(db: Session, query: str | None) -> SearchResult:
    """Patients whose record number equals the query, or whose name contains every word of
    it, ignoring case; active and inactive patients, ordered by name."""
    search = parse_search(query)
    statement = select(Patient).order_by(func.lower(Patient.full_name), Patient.id)
    if search.record_id is not None:
        statement = statement.where(Patient.id == search.record_id)
    else:
        for word in search.words:
            statement = statement.where(Patient.full_name.ilike(_contains(word), escape="\\"))
    found = list(db.scalars(statement.limit(SEARCH_LIMIT + 1)))
    return SearchResult(found[:SEARCH_LIMIT], len(found) > SEARCH_LIMIT)
