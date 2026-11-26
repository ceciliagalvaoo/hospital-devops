"""JSON API for doctor profiles: registration (US-02).

Administrators only, following the RBAC matrix (docs/requirements.md §2.2); receptionists and
doctors receive HTTP 403.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.access import DbSession, require_roles
from app.doctors import InvalidDoctor, register_doctor, validate_doctor
from app.models import Doctor, Role, StaffAccount

router = APIRouter(prefix="/api/doctors", tags=["doctors"])

INVALID_DOCTOR = "Invalid doctor data."

Administrator = Annotated[StaffAccount, Depends(require_roles(Role.ADMINISTRATOR))]


def doctor_response(doctor: Doctor) -> dict:
    return {
        "id": doctor.id,
        "login": doctor.account.login,
        "full_name": doctor.full_name,
        "specialisation": doctor.specialisation.value,
        "is_active": doctor.is_active,
        "availability": [
            {
                "weekday": r.weekday,
                "start": r.start_time.strftime("%H:%M"),
                "end": r.end_time.strftime("%H:%M"),
            }
            for r in doctor.availability
        ],
    }


@router.post("", status_code=status.HTTP_201_CREATED, response_model=None)
def register(
    db: DbSession,
    account: Administrator,
    staff_account_id: Annotated[str, Form()] = "",
    full_name: Annotated[str, Form()] = "",
    specialisation: Annotated[str, Form()] = "",
    weekday: Annotated[list[str] | None, Form()] = None,
    start_time: Annotated[list[str] | None, Form()] = None,
    end_time: Annotated[list[str] | None, Form()] = None,
) -> dict | Response:
    """Register a doctor profile. The availability is sent as repeated ``weekday``
    (0 = Monday), ``start_time`` and ``end_time`` fields, one of each per range. Invalid data
    returns HTTP 422 with a message for each field or range."""
    try:
        details = validate_doctor(
            db,
            staff_account_id,
            full_name,
            specialisation,
            weekday or [],
            start_time or [],
            end_time or [],
        )
    except InvalidDoctor as invalid:
        return JSONResponse(
            {"detail": INVALID_DOCTOR, "errors": invalid.errors},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    return doctor_response(register_doctor(db, details))
