"""CSRF protection for every state-changing request.

A CSRF token is an HMAC of the request's binding cookie: the session cookie when the
request has one, otherwise the random pre-session cookie ``hospital_csrf``. A forged
cross-site request cannot read the cookies, so it cannot produce the token. Because the
session token changes on every login, so does the CSRF token.

The check runs as an application-wide dependency (see ``app.main``), so new routes are
protected by default. Safe methods are not checked and must not change state.
"""

import hashlib
import hmac
import secrets

from fastapi import HTTPException, Request, Response, status

from app.auth import SESSION_COOKIE_NAME, SESSION_LIFETIME, session_cookie_secure

CSRF_COOKIE_NAME = "hospital_csrf"
CSRF_FORM_FIELD = "csrf_token"
CSRF_HEADER = "X-CSRF-Token"
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
FORM_CONTENT_TYPES = ("application/x-www-form-urlencoded", "multipart/form-data")

INVALID_TOKEN = "CSRF token missing or invalid."
CROSS_ORIGIN = "Cross-origin request refused."

# Generated per process: a restart only invalidates forms that were open at that moment.
_KEY = secrets.token_bytes(32)


def _sign(binding: str) -> str:
    return hmac.new(_KEY, binding.encode("utf-8"), hashlib.sha256).hexdigest()


def _binding(request: Request) -> str | None:
    session = request.cookies.get(SESSION_COOKIE_NAME)
    if session:
        return f"session:{session}"
    pre_session = request.cookies.get(CSRF_COOKIE_NAME)
    if pre_session:
        return f"pre-session:{pre_session}"
    return None


def issue_token(request: Request, response: Response) -> str:
    """Return the CSRF token for this request, setting a pre-session cookie if needed."""
    binding = _binding(request)
    if binding is None:
        pre_session = secrets.token_urlsafe(32)
        response.set_cookie(
            CSRF_COOKIE_NAME,
            pre_session,
            max_age=int(SESSION_LIFETIME.total_seconds()),
            path="/",
            secure=session_cookie_secure(),
            httponly=True,
            samesite="lax",
        )
        binding = f"pre-session:{pre_session}"
    return _sign(binding)


def _is_cross_origin(request: Request) -> bool:
    origin = request.headers.get("origin")
    if origin is not None:
        return origin != f"{request.url.scheme}://{request.url.netloc}"
    return request.headers.get("sec-fetch-site") == "cross-site"


async def _submitted_token(request: Request) -> str | None:
    token = request.headers.get(CSRF_HEADER)
    if token:
        return token
    if request.headers.get("content-type", "").startswith(FORM_CONTENT_TYPES):
        value = (await request.form()).get(CSRF_FORM_FIELD)
        if isinstance(value, str):
            return value
    return None


async def csrf_protect(request: Request) -> None:
    """Refuse state-changing requests that are cross-origin or lack a valid CSRF token."""
    if request.method in SAFE_METHODS:
        return
    if _is_cross_origin(request):
        raise HTTPException(status.HTTP_403_FORBIDDEN, CROSS_ORIGIN)
    binding = _binding(request)
    token = await _submitted_token(request)
    if binding is None or token is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, INVALID_TOKEN)
    # Compared as bytes: compare_digest rejects non-ASCII str input with an error.
    if not hmac.compare_digest(token.encode("utf-8"), _sign(binding).encode("ascii")):
        raise HTTPException(status.HTTP_403_FORBIDDEN, INVALID_TOKEN)
