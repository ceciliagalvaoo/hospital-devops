"""Integration tests for the reusable authentication and role dependencies.

No application route is restricted by role yet, so a test-only router declares one
route per access requirement.
"""

from datetime import UTC, datetime, timedelta
from typing import Annotated

import pytest
from fastapi import APIRouter, Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.access import (
    NOT_AUTHENTICATED,
    NOT_PERMITTED,
    CurrentAccount,
    current_account,
    require_roles,
)
from app.auth import SESSION_COOKIE_NAME
from app.db import get_session
from app.main import app as application
from app.models import Role, StaffAccount, StaffSession
from app.routes import auth

PASSWORD = "synthetic-password"
UNAUTHENTICATED = {"detail": NOT_AUTHENTICATED}
FORBIDDEN = {"detail": NOT_PERMITTED}

FrontDeskAccount = Annotated[
    StaffAccount, Depends(require_roles(Role.RECEPTIONIST, Role.ADMINISTRATOR))
]

router = APIRouter()


@router.get("/signed-in")
def signed_in(account: CurrentAccount) -> dict[str, str]:
    return {"login": account.login}


@router.get("/administrators", dependencies=[Depends(require_roles(Role.ADMINISTRATOR))])
def administrators_only() -> dict[str, str]:
    return {"access": "granted"}


@router.get("/front-desk")
def front_desk(account: FrontDeskAccount) -> dict[str, str]:
    return {"login": account.login}


access_app = FastAPI()
access_app.include_router(auth.router)
access_app.include_router(router)

# Route -> roles that may use it. Every other role must be refused with HTTP 403.
RESTRICTED = {
    "/administrators": {Role.ADMINISTRATOR},
    "/front-desk": {Role.RECEPTIONIST, Role.ADMINISTRATOR},
}
ROLE_CASES = [(path, role) for path in RESTRICTED for role in Role]


@pytest.fixture
def client(db_session):
    access_app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(access_app) as test_client:
        yield test_client
    access_app.dependency_overrides.clear()


@pytest.fixture
def accounts(db_session) -> dict[Role, StaffAccount]:
    created = {}
    for role in Role:
        staff = StaffAccount(login=f"synthetic.{role.value}", role=role)
        staff.set_password(PASSWORD)
        db_session.add(staff)
        created[role] = staff
    db_session.commit()
    return created


def log_in_as(client, role: Role) -> None:
    response = client.post(
        "/auth/login", data={"login": f"synthetic.{role.value}", "password": PASSWORD}
    )
    assert response.status_code == 200


@pytest.mark.parametrize(("path", "role"), ROLE_CASES, ids=str)
def test_role_access_matches_the_route_requirement(client, accounts, path, role):
    log_in_as(client, role)

    response = client.get(path)

    if role in RESTRICTED[path]:
        assert response.status_code == 200
    else:
        assert response.status_code == 403
        assert response.json() == FORBIDDEN


@pytest.mark.parametrize("role", list(Role), ids=str)
def test_any_authenticated_role_passes_the_authentication_check(client, accounts, role):
    log_in_as(client, role)

    response = client.get("/signed-in")

    assert response.status_code == 200
    assert response.json() == {"login": f"synthetic.{role.value}"}


@pytest.mark.parametrize("path", ["/signed-in", *RESTRICTED])
def test_requests_without_a_session_receive_401_not_403(client, path):
    response = client.get(path)

    assert response.status_code == 401
    assert response.json() == UNAUTHENTICATED


@pytest.mark.parametrize("path", ["/signed-in", *RESTRICTED])
def test_unknown_session_token_receives_401(client, path):
    client.cookies.set(SESSION_COOKIE_NAME, "not-a-real-token")

    response = client.get(path)

    assert response.status_code == 401
    assert response.json() == UNAUTHENTICATED


@pytest.mark.parametrize("path", ["/signed-in", *RESTRICTED])
def test_expired_session_receives_401(client, accounts, db_session, path):
    log_in_as(client, Role.ADMINISTRATOR)
    stored = db_session.scalars(select(StaffSession)).one()
    stored.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    db_session.commit()

    response = client.get(path)

    assert response.status_code == 401
    assert response.json() == UNAUTHENTICATED


@pytest.mark.parametrize("path", ["/signed-in", *RESTRICTED])
def test_deactivated_account_receives_401(client, accounts, db_session, path):
    log_in_as(client, Role.ADMINISTRATOR)
    accounts[Role.ADMINISTRATOR].is_active = False
    db_session.commit()

    response = client.get(path)

    assert response.status_code == 401
    assert response.json() == UNAUTHENTICATED


def test_require_roles_needs_at_least_one_role():
    with pytest.raises(ValueError, match="at least one role"):
        require_roles()


def test_me_uses_the_authentication_dependency():
    # Replacing the dependency changes the answer of /auth/me, so the route relies on it.
    stand_in = StaffAccount(login="synthetic.stand-in", role=Role.DOCTOR)
    application.dependency_overrides[current_account] = lambda: stand_in
    try:
        response = TestClient(application).get("/auth/me")
    finally:
        application.dependency_overrides.pop(current_account, None)

    assert response.status_code == 200
    assert response.json() == {"login": "synthetic.stand-in", "role": "doctor"}
