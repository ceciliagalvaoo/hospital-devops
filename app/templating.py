"""Rendering of server-side pages with Jinja2.

Every page receives the CSRF token for its forms, the logged-in account (if any) and the
navigation for that account's role.
"""

from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

from app.csrf import new_token, set_pre_session_cookie
from app.models import StaffAccount
from app.navigation import areas_for

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def render(
    request: Request,
    template: str,
    context: dict | None = None,
    *,
    account: StaffAccount | None = None,
    status_code: int = 200,
) -> Response:
    token, pre_session = new_token(request)
    page_context = {
        "account": account,
        "navigation": areas_for(account.role) if account else [],
        "csrf_token": token,
        **(context or {}),
    }
    response = templates.TemplateResponse(request, template, page_context, status_code=status_code)
    if pre_session is not None:
        set_pre_session_cookie(response, pre_session)
    return response


def wants_html(request: Request) -> bool:
    """True for browser page requests, which list text/html in their Accept header."""
    return "text/html" in request.headers.get("accept", "")
