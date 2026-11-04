"""Container smoke checks for the Compose stack (US-22). Run with: pytest -m smoke"""

import pytest

pytestmark = pytest.mark.smoke


def test_database_migration_and_application_start(stack):
    db = stack.state("db")
    migrate = stack.state("migrate")
    app = stack.state("app")

    assert db["State"] == "running"
    assert db["Health"] == "healthy"
    assert migrate["State"] == "exited"
    assert migrate["ExitCode"] == 0
    assert app["State"] == "running"


def test_health_reports_working_database_connection(stack):
    status, body = stack.get_health()

    assert status == 200
    assert body == {"status": "ok", "database": "ok"}


def test_migrations_are_applied_to_latest_revision(stack):
    current = stack.compose("exec", "-T", "app", "alembic", "current").stdout

    assert "(head)" in current


def test_application_does_not_run_as_root(stack):
    uid = stack.compose("exec", "-T", "app", "id", "-u").stdout.strip()

    assert uid.isdigit()
    assert uid != "0"


def test_health_reports_unavailable_database_when_database_stops(stack):
    stack.get_health()
    stack.compose("stop", "db")
    try:
        status, body = stack.get_health()

        assert status == 503
        assert body == {"status": "error", "database": "unavailable"}
    finally:
        stack.compose("start", "db")
        stack.up()


def test_application_does_not_start_when_migration_fails(failing_migration_stack):
    result = failing_migration_stack.up(check=False)

    assert result.returncode != 0
    assert failing_migration_stack.state("migrate")["ExitCode"] == 1
    assert failing_migration_stack.state("app")["State"] != "running"
