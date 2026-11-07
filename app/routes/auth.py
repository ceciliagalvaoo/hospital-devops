from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, Response, status

from app.access import CurrentAccount, DbSession, SessionToken
from app.auth import (
    authenticate,
    clear_session_cookie,
    delete_session,
    set_session_cookie,
    start_session,
)
from app.csrf import issue_token

router = APIRouter(prefix="/auth", tags=["authentication"])

INVALID_CREDENTIALS = "Invalid login or password."


def _account_response(account) -> dict[str, str]:
    return {"login": account.login, "role": account.role.value}


@router.post("/login")
def login(
    response: Response,
    login: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: DbSession,
    session_token: SessionToken = None,
) -> dict[str, str]:
    account = authenticate(db, login, password)
    if account is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, INVALID_CREDENTIALS)
    set_session_cookie(response, start_session(db, account, session_token))
    return _account_response(account)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, db: DbSession, session_token: SessionToken = None) -> None:
    if session_token:
        delete_session(db, session_token)
        db.commit()
    clear_session_cookie(response)


@router.get("/me")
def me(account: CurrentAccount) -> dict[str, str]:
    return _account_response(account)


@router.get("/csrf")
def csrf(request: Request, response: Response) -> dict[str, str]:
    """Return the CSRF token for the next state-changing request of this browser."""
    return {"csrf_token": issue_token(request, response)}
