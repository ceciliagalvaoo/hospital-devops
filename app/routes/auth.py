from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Form, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.auth import (
    SESSION_COOKIE_NAME,
    SESSION_LIFETIME,
    authenticate,
    create_session,
    delete_session,
    get_session_account,
    session_cookie_secure,
)
from app.db import get_session

router = APIRouter(prefix="/auth", tags=["authentication"])

INVALID_CREDENTIALS = "Invalid login or password."

DbSession = Annotated[Session, Depends(get_session)]
SessionToken = Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)]


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
def me(db: DbSession, session_token: SessionToken = None) -> dict[str, str]:
    account = get_session_account(db, session_token)
    if account is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated.")
    return _account_response(account)
