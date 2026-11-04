"""Integration tests for the staff account model and its migration."""

import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from app.db import Base
from app.models import Role, StaffAccount


def make_account(login: str = "synthetic.receptionist", role: Role = Role.RECEPTIONIST):
    account = StaffAccount(login=login, role=role)
    account.set_password("synthetic-password")
    return account


@pytest.mark.parametrize("role", list(Role))
def test_account_is_saved_with_each_supported_role(db_session, role):
    db_session.add(make_account(login=f"synthetic.{role.value}", role=role))
    db_session.commit()

    saved = db_session.scalars(select(StaffAccount).where(StaffAccount.role == role)).one()
    assert saved.login == f"synthetic.{role.value}"
    assert saved.is_active is True
    assert saved.created_at is not None


def test_only_the_password_hash_is_stored(db_session):
    db_session.add(make_account())
    db_session.commit()

    stored = db_session.execute(text("SELECT password_hash FROM staff_accounts")).scalar_one()
    assert stored.startswith("$2b$")
    assert "synthetic-password" not in stored
    assert db_session.scalars(select(StaffAccount)).one().check_password("synthetic-password")


def test_login_must_be_unique(db_session):
    db_session.add(make_account(login="synthetic.duplicate"))
    db_session.commit()
    db_session.add(make_account(login="synthetic.duplicate", role=Role.DOCTOR))

    with pytest.raises(IntegrityError, match="uq_staff_accounts_login"):
        db_session.commit()


def test_unsupported_role_is_rejected_by_the_database(db_session):
    with pytest.raises(IntegrityError, match="ck_staff_accounts_staff_role"):
        db_session.execute(
            text(
                "INSERT INTO staff_accounts (login, password_hash, role) "
                "VALUES ('synthetic.patient', 'not-a-real-hash', 'patient')"
            )
        )


def test_inactive_status_is_stored(db_session):
    account = make_account()
    account.is_active = False
    db_session.add(account)
    db_session.commit()

    assert db_session.scalars(select(StaffAccount)).one().is_active is False


def test_models_match_the_migrations(db_engine):
    with db_engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection), Base.metadata)

    assert differences == []
