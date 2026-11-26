"""Unit tests for the staff account creation rules (T-14.1). Synthetic data only."""

import pytest

from app.accounts import (
    MESSAGES,
    AccountDetails,
    InvalidAccount,
    normalise_login,
    validate_account,
)
from app.models import Role

PASSWORD = "synthetic-password-1"  # 20 characters


class NoAccounts:
    """Stands in for the database session: no login is taken."""

    def scalar(self, statement):
        return None


def validate(login="new.receptionist", role="receptionist", password=PASSWORD, confirmation=None):
    return validate_account(NoAccounts(), login, role, password, confirmation)


def errors_of(**fields) -> dict[str, str]:
    with pytest.raises(InvalidAccount) as raised:
        validate(**fields)
    return raised.value.errors


def test_valid_details_are_cleaned():
    assert validate(login="  New.Receptionist ") == AccountDetails(
        "new.receptionist", Role.RECEPTIONIST, PASSWORD
    )


@pytest.mark.parametrize(
    ("raw", "stored"), [("Dev.Doctor", "dev.doctor"), (" ADMIN_2 ", "admin_2"), (None, "")]
)
def test_logins_are_normalised_to_lower_case(raw, stored):
    assert normalise_login(raw) == stored


@pytest.mark.parametrize("login", ["abc", "a" * 64, "e2e.receptionist", "night-shift_01", "7up"])
def test_accepted_logins(login):
    assert validate(login=login).login == login


@pytest.mark.parametrize(
    "login", ["ab", "a" * 65, ".dot", "-dash", "with space", "josé", "a/b", "a@b"]
)
def test_rejected_logins(login):
    assert errors_of(login=login) == {"login": MESSAGES["login_invalid"]}


def test_every_role_is_supported_and_others_are_not():
    assert [validate(role=role.value).role for role in Role] == list(Role)
    for role in ["", "patient", "Administrator", "admin"]:
        assert errors_of(role=role) == {"role": MESSAGES["role_invalid"]}


def test_password_length_limits():
    # Written out rather than read from the code, so a changed limit fails this test.
    assert validate(password="x" * 12).password == "x" * 12
    assert validate(password="x" * 72).password == "x" * 72
    assert errors_of(password="") == {"password": MESSAGES["password_missing"]}
    assert errors_of(password="x" * 11) == {"password": MESSAGES["password_too_short"]}
    assert errors_of(password="x" * 73) == {"password": MESSAGES["password_too_long"]}
    assert errors_of(password="é" * 37) == {"password": MESSAGES["password_too_long"]}  # 74 bytes


def test_the_confirmation_is_checked_only_when_given():
    assert validate(confirmation=PASSWORD).password == PASSWORD
    assert errors_of(confirmation="another-password") == {
        "password_confirmation": MESSAGES["password_mismatch"]
    }


def test_every_invalid_field_is_reported_at_once():
    assert errors_of(login="", role="", password="short") == {
        "login": MESSAGES["login_missing"],
        "role": MESSAGES["role_invalid"],
        "password": MESSAGES["password_too_short"],
    }
