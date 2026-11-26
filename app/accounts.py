"""Staff account creation rules (US-14), shared by the JSON API and the pages.

Logins are normalised to lower case, here and at login (app/auth.py), so "Dev.Doctor" and
"dev.doctor" are the same account (decided in the Sprint 2 planning after the Sprint 1
review). Every invalid field is reported at once.
"""

import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Role, StaffAccount
from app.security import MAX_PASSWORD_BYTES

LOGIN_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")  # 3 to 64 characters
PASSWORD_MIN_LENGTH = 12

MESSAGES = {
    "login_missing": "Enter a login.",
    "login_invalid": (
        "Use 3 to 64 letters, digits, dots, hyphens or underscores, "
        "starting with a letter or a digit."
    ),
    "login_taken": "This login is already used by another account.",
    "role_invalid": "Choose one of the roles: receptionist, doctor or administrator.",
    "password_missing": "Enter a password.",
    "password_too_short": f"The password must have at least {PASSWORD_MIN_LENGTH} characters.",
    "password_too_long": f"The password can have at most {MAX_PASSWORD_BYTES} bytes.",
    "password_mismatch": "The two passwords do not match.",
}


def normalise_login(login: str | None) -> str:
    """The form in which logins are stored and compared."""
    return (login or "").strip().lower()


@dataclass(frozen=True)
class AccountDetails:
    login: str
    role: Role
    password: str


class InvalidAccount(ValueError):
    """The submitted account data is invalid; ``errors`` maps each field to its message."""

    def __init__(self, errors: dict[str, str]) -> None:
        super().__init__("Invalid account data.")
        self.errors = errors


def validate_account(
    db: Session,
    login: str | None,
    role: str | None,
    password: str | None,
    password_confirmation: str | None = None,
) -> AccountDetails:
    """Return the cleaned account details, or raise InvalidAccount listing every bad field.
    ``password_confirmation`` is checked when given (the form asks for it, the API does not)."""
    errors: dict[str, str] = {}

    name = normalise_login(login)
    if not name:
        errors["login"] = MESSAGES["login_missing"]
    elif not LOGIN_PATTERN.match(name):
        errors["login"] = MESSAGES["login_invalid"]
    elif db.scalar(select(StaffAccount.id).where(StaffAccount.login == name)) is not None:
        errors["login"] = MESSAGES["login_taken"]

    chosen = (role or "").strip()
    if chosen not in {item.value for item in Role}:
        errors["role"] = MESSAGES["role_invalid"]

    secret = password or ""
    if not secret:
        errors["password"] = MESSAGES["password_missing"]
    elif len(secret) < PASSWORD_MIN_LENGTH:
        errors["password"] = MESSAGES["password_too_short"]
    elif len(secret.encode("utf-8")) > MAX_PASSWORD_BYTES:
        errors["password"] = MESSAGES["password_too_long"]
    elif password_confirmation is not None and password_confirmation != secret:
        errors["password_confirmation"] = MESSAGES["password_mismatch"]

    if errors:
        raise InvalidAccount(errors)
    return AccountDetails(name, Role(chosen), secret)


def create_account(db: Session, details: AccountDetails) -> StaffAccount:
    """Save a new active account; only the bcrypt hash of the password is stored. A login
    taken between the check and the insert is reported like any other duplicate."""
    account = StaffAccount(login=details.login, role=details.role)
    account.set_password(details.password)
    db.add(account)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise InvalidAccount({"login": MESSAGES["login_taken"]}) from error
    return account
