"""Tests for the development-only staff account seed command."""

import pytest
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app import seed
from app.db import get_engine
from app.models import Role, StaffAccount

PASSWORD = "synthetic-seed-password"


def test_seed_creates_one_active_account_per_role(db_session):
    results = seed.seed_staff_accounts(db_session, PASSWORD)
    db_session.commit()

    accounts = db_session.scalars(select(StaffAccount)).all()
    assert {account.role for account in accounts} == set(Role)
    assert all(account.is_active for account in accounts)
    assert all(account.check_password(PASSWORD) for account in accounts)
    assert all(created for _, created in results)


def test_seed_does_not_duplicate_accounts_or_change_passwords(db_session):
    seed.seed_staff_accounts(db_session, PASSWORD)
    db_session.commit()
    hashes = {a.login: a.password_hash for a in db_session.scalars(select(StaffAccount))}

    results = seed.seed_staff_accounts(db_session, "another-synthetic-password")
    db_session.commit()

    accounts = db_session.scalars(select(StaffAccount)).all()
    assert len(accounts) == len(seed.DEV_ACCOUNTS)
    assert {a.login: a.password_hash for a in accounts} == hashes
    assert not any(created for _, created in results)


@pytest.mark.parametrize("app_env", [None, "production", "test"])
def test_main_refuses_outside_development(monkeypatch, capsys, app_env):
    if app_env is None:
        monkeypatch.delenv("APP_ENV", raising=False)
    else:
        monkeypatch.setenv("APP_ENV", app_env)
    monkeypatch.setenv("SEED_PASSWORD", PASSWORD)

    assert seed.main() == 1
    assert "APP_ENV=development" in capsys.readouterr().err


def test_main_refuses_without_seed_password(monkeypatch, capsys):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("SEED_PASSWORD", raising=False)

    assert seed.main() == 1
    assert "SEED_PASSWORD" in capsys.readouterr().err


def test_main_seeds_the_configured_database(app_uses_test_database, monkeypatch, capsys):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("SEED_PASSWORD", PASSWORD)
    logins = [login for login, _ in seed.DEV_ACCOUNTS]
    try:
        assert seed.main() == 0
        output = capsys.readouterr().out
        assert all(f"created  {login}" in output for login in logins)
    finally:
        with Session(get_engine()) as session:
            session.execute(delete(StaffAccount).where(StaffAccount.login.in_(logins)))
            session.commit()
