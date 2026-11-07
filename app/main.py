from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import Response

from app.access import NOT_PERMITTED
from app.csrf import CROSS_ORIGIN, INVALID_TOKEN, csrf_protect
from app.routes import auth, health, pages
from app.templating import render, wants_html

# Title and message of the browser error page for each API detail text, so that the
# title states the actual reason instead of a generic one for every status code.
PAGE_ERRORS = {
    NOT_PERMITTED: ("Access denied", "Your role does not have access to this page."),
    INVALID_TOKEN: (
        "Form expired",
        "The form has expired. Go back, reload the page and try again.",
    ),
    CROSS_ORIGIN: ("Request refused", "The request came from another site and was refused."),
    "Not Found": ("Page not found", "This page does not exist."),
}
GENERIC_ERROR_TITLE = "Something went wrong"
LOGIN_NOTICE = "Please log in to continue."

# CSRF protection applies to every route; safe methods pass through unchecked.
app = FastAPI(title="Hospital Management", dependencies=[Depends(csrf_protect)])
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(pages.router)


@app.exception_handler(StarletteHTTPException)
async def page_errors(request: Request, exc: StarletteHTTPException) -> Response:
    """Browsers receive pages for errors; API clients keep the JSON responses."""
    if not wants_html(request):
        return await http_exception_handler(request, exc)
    if exc.status_code == 401:
        return render(request, "login.html", {"notice": LOGIN_NOTICE}, status_code=401)
    title, message = PAGE_ERRORS.get(exc.detail, (GENERIC_ERROR_TITLE, exc.detail))
    return render(
        request,
        "error.html",
        {"title": title, "message": message},
        account=getattr(request.state, "account", None),
        status_code=exc.status_code,
    )
