"""JSON API for patient records: registration (US-03) and search (US-09).

Receptionists and administrators only, following the RBAC matrix (docs/requirements.md §2.2);
doctors receive HTTP 403."""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, status
from fastapi.responses import JSONResponse
from starlette.responses import Response

from app.access import DbSession, require_roles
from app.models import Patient, Role, StaffAccount
from app.patients import (
    InvalidPatient,
    InvalidSearch,
    register_patient,
    search_patients,
    validate_patient,
)

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


@router.get("", response_model=None)
def search(
    db: DbSession, account: PatientStaff, q: Annotated[str, Query()] = ""
) -> dict | Response:
    """Search by record number (P-000042) or by words of the name. An empty or too short
    query returns HTTP 422 with the message to show."""
    try:
        result = search_patients(db, q)
    except InvalidSearch as invalid:
        return JSONResponse(
            {"detail": invalid.message}, status_code=status.HTTP_422_UNPROCESSABLE_CONTENT
        )
    return {"patients": [patient_response(p) for p in result.patients], "more": result.more}
