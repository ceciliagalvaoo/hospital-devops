"""JSON API for staff accounts: creation (US-14).

Administrators only, following the RBAC matrix (docs/requirements.md §2.2); receptionists and
doctors receive HTTP 403.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.access import DbSession, require_roles
from app.accounts import InvalidAccount, create_account, validate_account
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
