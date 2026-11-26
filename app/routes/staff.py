"""JSON API for staff accounts: creation (US-14) and deactivation (US-15).

Administrators only, following the RBAC matrix (docs/requirements.md §2.2); receptionists and
doctors receive HTTP 403.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.access import DbSession, require_roles
from app.accounts import (
    CannotDeactivate,
    InvalidAccount,
    create_account,
    deactivate_account,
    validate_account,
)
from app.models import Role, StaffAccount

router = APIRouter(prefix="/api/staff", tags=["staff accounts"])

INVALID_ACCOUNT = "Invalid account data."

Administrator = Annotated[StaffAccount, Depends(require_roles(Role.ADMINISTRATOR))]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=None)
def create(
    db: DbSession,
    account: Administrator,
    login: Annotated[str, Form()] = "",
    role: Annotated[str, Form()] = "",
    password: Annotated[str, Form()] = "",
) -> dict | Response:
    """Create an active staff account. Invalid data returns HTTP 422 with a message for each
    field; the password is never returned."""
    try:
        created = create_account(db, validate_account(db, login, role, password))
    except InvalidAccount as invalid:
        return JSONResponse(
            {"detail": INVALID_ACCOUNT, "errors": invalid.errors},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    return {"login": created.login, "role": created.role.value, "is_active": created.is_active}


@router.post("/{account_id}/deactivate", response_model=None)
def deactivate(db: DbSession, account: Administrator, account_id: int) -> dict | Response:
    """Deactivate a staff account: it can no longer log in and its sessions end. HTTP 200 with
    the account, also when it was already inactive; HTTP 409 for the administrator's own
    account; HTTP 404 for an unknown account."""
    target = db.get(StaffAccount, account_id)
    if target is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not Found")
    try:
        deactivate_account(db, target, by=account)
    except CannotDeactivate as refused:
        return JSONResponse({"detail": refused.message}, status_code=status.HTTP_409_CONFLICT)
    return {"login": target.login, "role": target.role.value, "is_active": target.is_active}
