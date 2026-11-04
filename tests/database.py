"""Helpers for the isolated PostgreSQL test database."""

import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import make_url

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEST_DATABASE_URL = (
    "postgresql+psycopg://hospital_test:hospital_test@127.0.0.1:5433/hospital_test"
)
START_HINT = "Start it with: docker compose --profile test up -d --wait test-db"


def get_test_database_url() -> str:
    return os.environ.get("TEST_DATABASE_URL", DEFAULT_TEST_DATABASE_URL)


def ensure_test_database(url: str) -> None:
    """Refuse to run against a database that is not clearly a test database."""
    database = make_url(url).database or ""
    if "test" not in database:
        raise RuntimeError(
            f"Refusing to use database {database!r}: the test database name must contain 'test'."
        )


def run_migrations(url: str, direction: str, revision: str) -> None:
    """Run Alembic against the test database; migrations/env.py reads DATABASE_URL."""
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = url
    try:
        operation = command.upgrade if direction == "upgrade" else command.downgrade
        operation(Config(str(ROOT / "alembic.ini")), revision)
    finally:
        if previous is None:
            del os.environ["DATABASE_URL"]
        else:
            os.environ["DATABASE_URL"] = previous
