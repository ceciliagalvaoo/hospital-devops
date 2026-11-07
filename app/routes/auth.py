from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Request, Response, status

from app.access import CurrentAccount, DbSession, SessionToken
from app.auth import (
    SESSION_COOKIE_NAME,
    SESSION_LIFETIME,
    authenticate,
    create_session,
    delete_session,
    session_cookie_secure,
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
    if session_token:
        delete_session(db, session_token)
    token = create_session(db, account)
    db.commit()
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        max_age=int(SESSION_LIFETIME.total_seconds()),
        path="/",
        secure=session_cookie_secure(),
        httponly=True,
        samesite="lax",
    )
    return _account_response(account)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response, db: DbSession, session_token: SessionToken = None) -> None:
    if session_token:
        delete_session(db, session_token)
        db.commit()
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        path="/",
        secure=session_cookie_secure(),
        httponly=True,
        samesite="lax",
    )


@router.get("/me")
def me(account: CurrentAccount) -> dict[str, str]:
    return _account_response(account)


@router.get("/csrf")
def csrf(request: Request, response: Response) -> dict[str, str]:
    """Return the CSRF token for the next state-changing request of this browser."""
    return {"csrf_token": issue_token(request, response)}
