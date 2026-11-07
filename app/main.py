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

# Messages shown on the browser error page instead of the API detail text.
PAGE_MESSAGES = {
    NOT_PERMITTED: "Your role does not have access to this page.",
    INVALID_TOKEN: "The form has expired. Go back, reload the page and try again.",
    CROSS_ORIGIN: "The request came from another site and was refused.",
    "Not Found": "This page does not exist.",
}
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
    message = PAGE_MESSAGES.get(exc.detail, exc.detail)
    return render(
        request,
        "error.html",
        {"status_code": exc.status_code, "message": message},
        account=getattr(request.state, "account", None),
        status_code=exc.status_code,
    )
