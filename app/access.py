"""Reusable FastAPI dependencies that enforce authentication and role permissions.

Routes declare what they require instead of checking the session themselves:

    @router.get("/accounts")
    def list_accounts(account: Annotated[StaffAccount, Depends(require_roles(Role.ADMINISTRATOR))]):
        ...

Unauthenticated requests receive HTTP 401; authenticated accounts without a permitted
role receive HTTP 403 (README §3.4).
"""

from collections.abc import Callable
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth import SESSION_COOKIE_NAME, get_session_account
from app.db import get_session
from app.models import Role, StaffAccount

NOT_AUTHENTICATED = "Not authenticated."
NOT_PERMITTED = "Not permitted for this role."

DbSession = Annotated[Session, Depends(get_session)]
SessionToken = Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)]


def current_account(
    request: Request, db: DbSession, session_token: SessionToken = None
) -> StaffAccount:
    """Return the account of the valid session, or reject the request with HTTP 401.

    The account is also kept on ``request.state`` so that error pages can show the
    navigation of the logged-in user.
    """
    account = get_session_account(db, session_token)
    if account is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, NOT_AUTHENTICATED)
    request.state.account = account
    return account


CurrentAccount = Annotated[StaffAccount, Depends(current_account)]


def require_roles(*roles: Role) -> Callable[[StaffAccount], StaffAccount]:
    """Build a dependency that admits only authenticated accounts with one of the roles."""
    if not roles:
        raise ValueError("require_roles needs at least one role.")
    permitted = frozenset(roles)

    def check_role(account: CurrentAccount) -> StaffAccount:
        if account.role not in permitted:
            raise HTTPException(status.HTTP_403_FORBIDDEN, NOT_PERMITTED)
        return account

    return check_role
