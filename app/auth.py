"""Credential checks and server-side session handling."""

import hashlib
import os
import secrets
from datetime import UTC, datetime, timedelta
from functools import lru_cache

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import StaffAccount, StaffSession
from app.security import hash_password, verify_password

SESSION_COOKIE_NAME = "hospital_session"
SESSION_LIFETIME = timedelta(hours=8)


def session_cookie_secure() -> bool:
    """Mark the cookie Secure when the application is served over HTTPS."""
    return os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


@lru_cache
def _dummy_password_hash() -> str:
    return hash_password("timing-equaliser")


def authenticate(db: Session, login: str, password: str) -> StaffAccount | None:
    """Return the active account matching the credentials, or None.

    A password check always runs, so unknown logins take as long as known ones.
    """
    account = db.scalar(select(StaffAccount).where(StaffAccount.login == login))
    if account is None:
        verify_password(password, _dummy_password_hash())
        return None
    if not account.check_password(password) or not account.is_active:
        return None
    return account


def create_session(db: Session, account: StaffAccount) -> str:
    """Store a new session and return its token for the cookie."""
    token = secrets.token_urlsafe(32)
    db.add(
        StaffSession(
            token_hash=hash_token(token),
            account=account,
            expires_at=datetime.now(UTC) + SESSION_LIFETIME,
        )
    )
    return token


def delete_session(db: Session, token: str) -> None:
    db.execute(delete(StaffSession).where(StaffSession.token_hash == hash_token(token)))


def get_session_account(db: Session, token: str | None) -> StaffAccount | None:
    """Return the account of a valid session; expired sessions and inactive accounts fail."""
    if not token:
        return None
    session = db.scalar(select(StaffSession).where(StaffSession.token_hash == hash_token(token)))
    if session is None:
        return None
    if session.expires_at <= datetime.now(UTC) or not session.account.is_active:
        db.delete(session)
        db.commit()
        return None
    return session.account
