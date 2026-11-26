"""Staff account pages: the account list and the creation form (US-14), and the deactivation
confirmation (US-15).

Administrators only, like the API (docs/requirements.md §2.2). The form applies the rules of
app/accounts.py and also asks for the password twice. Passwords are never sent back to the
browser, not even after an error.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from starlette.responses import Response

from app.access import DbSession, require_roles
from app.accounts import (
    OWN_ACCOUNT,
    CannotDeactivate,
    InvalidAccount,
    create_account,
    deactivate_account,
    validate_account,
)
from app.models import Role, StaffAccount
from app.templating import render

router = APIRouter(include_in_schema=False)

Administrator = Annotated[StaffAccount, Depends(require_roles(Role.ADMINISTRATOR))]

ROLES = [(role.value, role.value.capitalize()) for role in Role]


@router.get("/staff")
def staff_area(
    request: Request,
    db: DbSession,
    account: Administrator,
    created: int | None = None,
    deactivated: int | None = None,
) -> Response:
    accounts = db.scalars(select(StaffAccount).order_by(StaffAccount.login)).all()
    context = {
        "accounts": accounts,
        "created": db.get(StaffAccount, created) if created else None,
        "deactivated": db.get(StaffAccount, deactivated) if deactivated else None,
    }
    return render(request, "staff.html", context, account=account)


def _account_or_404(db: DbSession, account_id: int) -> StaffAccount:
    target = db.get(StaffAccount, account_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not Found")
    return target


def _confirmation(request, account, target, refused=None, status_code=status.HTTP_200_OK):
    context = {"target": target, "refused": refused}
    return render(
        request, "staff_deactivate.html", context, account=account, status_code=status_code
    )


@router.get("/staff/{account_id:int}/deactivate")
def deactivate_confirmation(
    request: Request, db: DbSession, account: Administrator, account_id: int
) -> Response:
    """Ask for confirmation before deactivating; explain when it is not possible."""
    target = _account_or_404(db, account_id)
    if target.id == account.id:
        return _confirmation(request, account, target, OWN_ACCOUNT, status.HTTP_409_CONFLICT)
    return _confirmation(request, account, target)


@router.post("/staff/{account_id:int}/deactivate")
def deactivate_submit(
    request: Request, db: DbSession, account: Administrator, account_id: int
) -> Response:
    target = _account_or_404(db, account_id)
    try:
        deactivate_account(db, target, by=account)
    except CannotDeactivate as refused:
        return _confirmation(request, account, target, refused.message, status.HTTP_409_CONFLICT)
    # Post/Redirect/Get: reloading the confirmation never submits twice.
    return RedirectResponse(f"/staff?deactivated={target.id}", status.HTTP_303_SEE_OTHER)


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
