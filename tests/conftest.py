"""Shared fixtures for integration tests that use the isolated PostgreSQL test database."""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from tests.database import (
    START_HINT,
    ensure_test_database,
    get_test_database_url,
    run_migrations,
)


@pytest.fixture(scope="session")
def db_engine() -> Engine:
    """Engine for the test database, migrated to the latest revision for the whole session."""
    url = get_test_database_url()
    ensure_test_database(url)
    engine = create_engine(url, connect_args={"connect_timeout": 3})
    try:
        with engine.connect():
            pass
    except OperationalError as error:
        engine.dispose()
        message = f"Test database is not reachable. {START_HINT}"
        if os.environ.get("CI") == "true":
            pytest.fail(f"{message}\n{error}")
        pytest.skip(message)

    run_migrations(url, "upgrade", "head")
    try:
        yield engine
    finally:
        run_migrations(url, "downgrade", "base")
        engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine):
    """Session inside a transaction that is rolled back after each test."""
    with db_engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()


@pytest.fixture
def app_uses_test_database(db_engine: Engine, monkeypatch):
    """Point the application's DATABASE_URL at the test database for one test."""
    from app import db

    monkeypatch.setenv("DATABASE_URL", get_test_database_url())
    db.get_engine.cache_clear()
    yield
    db.get_engine.cache_clear()


def pytest_collection_modifyitems(items):
    """Mark every test that uses the test database as an integration test, and run the
    end-to-end tests last: their accounts are committed for the whole session, so tests
    that count rows must run before them when both are selected."""
    for item in items:
        if "db_engine" in getattr(item, "fixturenames", ()):
            item.add_marker(pytest.mark.integration)
    items.sort(key=lambda item: item.get_closest_marker("e2e") is not None)
