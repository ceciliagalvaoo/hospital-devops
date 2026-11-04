"""Integration tests for the isolated test-database fixtures."""

import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi.testclient import TestClient
from sqlalchemy import inspect, text

from app.main import app
from tests.database import ROOT, ensure_test_database


def test_migrations_are_applied_to_test_database(db_session):
    revision = db_session.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
    head = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini"))).get_current_head()

    assert revision == head


def test_session_uses_dedicated_test_database(db_session):
    database = db_session.execute(text("SELECT current_database()")).scalar_one()

    assert "test" in database


@pytest.mark.parametrize("run", ["first", "second"])
def test_changes_are_rolled_back_between_tests(db_session, run):
    # Whichever run executes second fails if the first run's table leaked.
    assert not inspect(db_session.connection()).has_table("isolation_probe")

    db_session.execute(text("CREATE TABLE isolation_probe (value text)"))
    db_session.execute(text("INSERT INTO isolation_probe VALUES (:value)"), {"value": run})
    db_session.commit()

    assert db_session.execute(text("SELECT value FROM isolation_probe")).scalar_one() == run


def test_health_reports_database_ok_against_test_database(app_uses_test_database):
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


@pytest.mark.parametrize(
    "url",
    [
        "postgresql+psycopg://hospital:secret@db:5432/hospital",
        "postgresql+psycopg://user:secret@localhost:5432/postgres",
    ],
)
def test_non_test_database_is_refused(url):
    with pytest.raises(RuntimeError, match="must contain 'test'"):
        ensure_test_database(url)
