"""Staff account pages (US-14): the account list and the creation form.

Administrators only, like the API (docs/requirements.md §2.2). The form applies the rules of
app/accounts.py and also asks for the password twice. Passwords are never sent back to the
browser, not even after an error.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from starlette.responses import Response

from app.access import DbSession, require_roles
from app.accounts import InvalidAccount, create_account, validate_account
from app.models import Role, StaffAccount
from app.templating import render

router = APIRouter(include_in_schema=False)

Administrator = Annotated[StaffAccount, Depends(require_roles(Role.ADMINISTRATOR))]

ROLES = [(role.value, role.value.capitalize()) for role in Role]


@router.get("/staff")
def staff_area(
    request: Request, db: DbSession, account: Administrator, created: int | None = None
) -> Response:
    accounts = db.scalars(select(StaffAccount).order_by(StaffAccount.login)).all()
    new_account = db.get(StaffAccount, created) if created else None
    context = {"accounts": accounts, "created": new_account}
    return render(request, "staff.html", context, account=account)


def _form(request, account, values, errors, status_code=status.HTTP_200_OK) -> Response:
    context = {"roles": ROLES, "values": values, "errors": errors}
    return render(request, "staff_form.html", context, account=account, status_code=status_code)


@router.get("/staff/new")
def creation_form(request: Request, account: Administrator) -> Response:
    return _form(request, account, {}, {})


@router.post("/staff/new")
def creation_submit(
    request: Request,
    db: DbSession,
    account: Administrator,
    login: Annotated[str, Form()] = "",
    role: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
    password_confirmation: Annotated[str, Form()] = "",
) -> Response:
    try:
        details = validate_account(db, login, role, password, password_confirmation)
        created = create_account(db, details)
    except InvalidAccount as invalid:
        values = {"login": login, "role": role}  # the passwords are not sent back
        return _form(
            request, account, values, invalid.errors, status.HTTP_422_UNPROCESSABLE_CONTENT
        )
    # Post/Redirect/Get: reloading the confirmation never creates the account twice.
    return RedirectResponse(f"/staff?created={created.id}", status.HTTP_303_SEE_OTHER)
