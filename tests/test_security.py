import pytest

from app.security import BCRYPT_ROUNDS, MAX_PASSWORD_BYTES, hash_password, verify_password


def test_hash_is_bcrypt_with_cost_factor_of_at_least_10():
    password_hash = hash_password("synthetic-password")

    prefix, cost = password_hash.split("$")[1:3]
    assert prefix == "2b"
    assert int(cost) == BCRYPT_ROUNDS >= 10


def test_hash_never_contains_the_plain_text_password():
    password_hash = hash_password("synthetic-password")

    assert "synthetic-password" not in password_hash


def test_same_password_produces_different_hashes():
    assert hash_password("synthetic-password") != hash_password("synthetic-password")


def test_verify_accepts_correct_and_rejects_wrong_password():
    password_hash = hash_password("synthetic-password")

    assert verify_password("synthetic-password", password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


@pytest.mark.parametrize("password", ["", "x" * (MAX_PASSWORD_BYTES + 1)])
def test_empty_or_too_long_password_is_rejected(password):
    with pytest.raises(ValueError):
        hash_password(password)


def test_verify_rejects_too_long_password_without_error():
    password_hash = hash_password("x" * MAX_PASSWORD_BYTES)

    assert verify_password("x" * (MAX_PASSWORD_BYTES + 1), password_hash) is False
