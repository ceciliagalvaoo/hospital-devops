"""JSON API for patient records (US-03). Receptionists and administrators only, following
the RBAC matrix (docs/requirements.md §2.2); doctors receive HTTP 403."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Form, status
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.access import DbSession, require_roles
from app.models import Patient, Role, StaffAccount
from app.patients import InvalidPatient, register_patient, validate_patient

router = APIRouter(prefix="/api/patients", tags=["patients"])

INVALID_PATIENT = "Invalid patient data."

PatientStaff = Annotated[
    StaffAccount, Depends(require_roles(Role.RECEPTIONIST, Role.ADMINISTRATOR))
]


def patient_response(patient: Patient) -> dict[str, str | bool | None]:
    return {
        "record_number": patient.record_number,
        "full_name": patient.full_name,
        "date_of_birth": patient.date_of_birth.isoformat(),
        "phone": patient.phone,
        "email": patient.email,
        "is_active": patient.is_active,
    }


@router.post("", status_code=status.HTTP_201_CREATED, response_model=None)
def register(
    db: DbSession,
    account: PatientStaff,
    full_name: Annotated[str, Form()] = "",
    date_of_birth: Annotated[str, Form()] = "",
    phone: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
) -> dict[str, str | bool | None] | Response:
    """Register a patient. Invalid data returns HTTP 422 with a message for each field."""
    try:
        details = validate_patient(full_name, date_of_birth, phone, email, today=date.today())
    except InvalidPatient as invalid:
        return JSONResponse(
            {"detail": INVALID_PATIENT, "errors": invalid.errors},
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    return patient_response(register_patient(db, details))
