"""Server-rendered pages: login, logout, home and the role-restricted areas."""

from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from starlette.responses import Response

from app.access import CurrentAccount, DbSession, SessionToken, require_roles
from app.auth import (
    authenticate,
    clear_session_cookie,
    delete_session,
    get_session_account,
    set_session_cookie,
    start_session,
)
from app.models import StaffAccount
from app.navigation import AREAS, Area
from app.routes.auth import INVALID_CREDENTIALS
from app.templating import render

router = APIRouter(include_in_schema=False)


@router.get("/login")
def login_page(request: Request, db: DbSession, session_token: SessionToken = None) -> Response:
    if get_session_account(db, session_token) is not None:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    return render(request, "login.html")


@router.post("/login")
def login_submit(
    request: Request,
    db: DbSession,
    login: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
    session_token: SessionToken = None,
) -> Response:
    account = authenticate(db, login, password)
    if account is None:
        return render(
            request,
            "login.html",
            {"error": INVALID_CREDENTIALS, "login": login},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    set_session_cookie(response, start_session(db, account, session_token))
    return response


@router.post("/logout")
def logout_submit(db: DbSession, session_token: SessionToken = None) -> Response:
    if session_token:
        delete_session(db, session_token)
        db.commit()
    response = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    clear_session_cookie(response)
    return response


@router.get("/")
def home(request: Request, account: CurrentAccount) -> Response:
    return render(request, "home.html", account=account)


def _area_page(area: Area) -> Callable[..., Response]:
    AreaAccount = Annotated[StaffAccount, Depends(require_roles(*sorted(area.roles)))]

    def area_page(request: Request, account: AreaAccount) -> Response:
        return render(request, "area.html", {"area": area}, account=account)

    return area_page


for _area in AREAS:
    router.add_api_route(_area.path, _area_page(_area), methods=["GET"], name=_area.title)
