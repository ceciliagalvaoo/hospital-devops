"""Live application server and synthetic accounts for the Playwright end-to-end tests.

The server runs in a background thread of the test process, on a free local port, against
the isolated test database. pytest-playwright's ``page`` fixture opens its pages relative
to ``base_url``.
"""

import os
import socket
import threading
import time
from dataclasses import dataclass

import pytest
import uvicorn
from sqlalchemy import delete
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app import db
from app.main import app
from app.models import Role, StaffAccount
from tests.database import get_test_database_url

PASSWORD = "synthetic-e2e-password"
STARTUP_TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class E2EAccount:
    login: str
    role: Role
    password: str = PASSWORD


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def e2e_accounts(db_engine: Engine) -> dict[Role, E2EAccount]:
    """One committed synthetic account per role, removed (with its sessions) afterwards."""
    accounts = {role: E2EAccount(f"e2e.{role.value}", role) for role in Role}
    with Session(db_engine) as session:
        for account in accounts.values():
            staff = StaffAccount(login=account.login, role=account.role)
            staff.set_password(account.password)
            session.add(staff)
        session.commit()
    yield accounts
    with Session(db_engine) as session:
        logins = [account.login for account in accounts.values()]
        session.execute(delete(StaffAccount).where(StaffAccount.login.in_(logins)))
        session.commit()


@pytest.fixture(scope="session")
def live_server(db_engine: Engine, e2e_accounts) -> str:
    """Run the application with Uvicorn against the test database and return its URL."""
    previous = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = get_test_database_url()
    db.get_engine.cache_clear()

    port = _free_port()
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
    while not server.started:
        if not thread.is_alive() or time.monotonic() > deadline:
            pytest.fail("The application server did not start.")
        time.sleep(0.05)

    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=10)
        if previous is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = previous
        db.get_engine.cache_clear()


@pytest.fixture(scope="session")
def base_url(live_server: str) -> str:
    """Point pytest-playwright's relative page.goto() calls at the live server."""
    return live_server
