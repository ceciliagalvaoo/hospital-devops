"""Patient pages: the patients area with search (US-09), the registration form and the
patient's record (US-03).

Receptionists and administrators only, like the API (docs/requirements.md §2.2). The form
applies the rules of app/patients.py, so the pages and the API accept exactly the same data.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from starlette.responses import Response

from app.access import DbSession, require_roles
from app.models import Patient, Role, StaffAccount
from app.patients import (
    EARLIEST_DATE_OF_BIRTH,
    SEARCH_LIMIT,
    InvalidPatient,
    InvalidSearch,
    register_patient,
    search_patients,
    validate_patient,
)
from app.templating import render

router = APIRouter(include_in_schema=False)

PatientStaff = Annotated[
    StaffAccount, Depends(require_roles(Role.RECEPTIONIST, Role.ADMINISTRATOR))
]


def _form(request: Request, account: StaffAccount, values: dict, errors: dict, status_code=200):
    return render(
        request,
        "patient_form.html",
        {
            "values": values,
            "errors": errors,
            "earliest": EARLIEST_DATE_OF_BIRTH.isoformat(),
            "today": date.today().isoformat(),
        },
        account=account,
        status_code=status_code,
    )


@router.get("/patients")
def patients_area(
    request: Request, db: DbSession, account: PatientStaff, q: str | None = None
) -> Response:
    """The patients area: a link to register a patient and the search. Without ``q`` only the
    form is shown; an unusable query returns the form with its message and HTTP 422."""
    context = {"query": q or "", "result": None, "error": None, "limit": SEARCH_LIMIT}
    status_code = status.HTTP_200_OK
    if q is not None:
        try:
            context["result"] = search_patients(db, q)
        except InvalidSearch as invalid:
            context["error"] = invalid.message
            status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
    return render(request, "patients.html", context, account=account, status_code=status_code)


@router.get("/patients/new")
def registration_form(request: Request, account: PatientStaff) -> Response:
    return _form(request, account, {}, {})


@router.post("/patients/new")
def registration_submit(
    request: Request,
    db: DbSession,
    account: PatientStaff,
    full_name: Annotated[str, Form()] = "",
    date_of_birth: Annotated[str, Form()] = "",
    phone: Annotated[str, Form()] = "",
    email: Annotated[str, Form()] = "",
) -> Response:
    values = {
        "full_name": full_name,
        "date_of_birth": date_of_birth,
        "phone": phone,
        "email": email,
    }
    try:
        details = validate_patient(full_name, date_of_birth, phone, email, today=date.today())
    except InvalidPatient as invalid:
        return _form(
            request, account, values, invalid.errors, status.HTTP_422_UNPROCESSABLE_CONTENT
        )
    patient = register_patient(db, details)
    # Post/Redirect/Get: reloading the confirmation never registers the patient twice.
    return RedirectResponse(
        f"/patients/{patient.id}?registered=1", status_code=status.HTTP_303_SEE_OTHER
    )


@router.get("/patients/{patient_id:int}")
def patient_record(
    request: Request,
    db: DbSession,
    account: PatientStaff,
    patient_id: int,
    registered: bool = False,
) -> Response:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not Found")
    return render(
        request, "patient.html", {"patient": patient, "registered": registered}, account=account
    )
