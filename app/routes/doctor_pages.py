"""Doctor pages (US-02): the doctors area, the registration form and the doctor's profile.

Administrators only, like the API (docs/requirements.md §2.2). The form applies the rules of
app/doctors.py, so the pages and the API accept exactly the same data.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from starlette.responses import Response

from app.access import DbSession, require_roles
from app.doctors import InvalidDoctor, eligible_accounts, register_doctor, validate_doctor
from app.models import Doctor, Role, Specialisation, StaffAccount, Weekday
from app.templating import render

router = APIRouter(include_in_schema=False)

Administrator = Annotated[StaffAccount, Depends(require_roles(Role.ADMINISTRATOR))]

FORM_ROWS = 6  # availability rows shown by the form; more ranges than rows can be added in US-13
SPECIALISATIONS = [(item.value, item.label) for item in Specialisation]
WEEKDAYS = [(item.value, item.label) for item in Weekday]


@router.get("/doctors")
def doctors_area(request: Request, db: DbSession, account: Administrator) -> Response:
    doctors = db.scalars(select(Doctor).order_by(func.lower(Doctor.full_name), Doctor.id)).all()
    return render(request, "doctors.html", {"doctors": doctors}, account=account)


def _form(request, db, account, values, rows, errors, status_code=status.HTTP_200_OK):
    rows = rows + [{"weekday": "", "start": "", "end": ""}] * max(0, FORM_ROWS - len(rows))
    context = {
        "accounts": [(str(a.id), a.login) for a in eligible_accounts(db)],
        "specialisations": SPECIALISATIONS,
        "weekdays": WEEKDAYS,
        "values": values,
        "rows": rows,
        "errors": errors,
    }
    return render(request, "doctor_form.html", context, account=account, status_code=status_code)


@router.get("/doctors/new")
def registration_form(request: Request, db: DbSession, account: Administrator) -> Response:
    return _form(request, db, account, {}, [], {})


@router.post("/doctors/new")
def registration_submit(
    request: Request,
    db: DbSession,
    account: Administrator,
    staff_account_id: Annotated[str, Form()] = "",
    full_name: Annotated[str, Form()] = "",
    specialisation: Annotated[str, Form()] = "",
    weekday: Annotated[list[str] | None, Form()] = None,
    start_time: Annotated[list[str] | None, Form()] = None,
    end_time: Annotated[list[str] | None, Form()] = None,
) -> Response:
    weekdays, starts, ends = weekday or [], start_time or [], end_time or []
    try:
        details = validate_doctor(
            db, staff_account_id, full_name, specialisation, weekdays, starts, ends
        )
    except InvalidDoctor as invalid:
        values = {
            "staff_account_id": staff_account_id,
            "full_name": full_name,
            "specialisation": specialisation,
        }
        count = max(len(weekdays), len(starts), len(ends))
        rows = [
            {
                "weekday": weekdays[i] if i < len(weekdays) else "",
                "start": starts[i] if i < len(starts) else "",
                "end": ends[i] if i < len(ends) else "",
            }
            for i in range(count)
        ]
        return _form(
            request,
            db,
            account,
            values,
            rows,
            invalid.errors,
            status.HTTP_422_UNPROCESSABLE_CONTENT,
        )
    doctor = register_doctor(db, details)
    # Post/Redirect/Get: reloading the confirmation never registers the doctor twice.
    return RedirectResponse(f"/doctors/{doctor.id}?registered=1", status.HTTP_303_SEE_OTHER)


@router.get("/doctors/{doctor_id:int}")
def doctor_profile(
    request: Request,
    db: DbSession,
    account: Administrator,
    doctor_id: int,
    registered: bool = False,
) -> Response:
    doctor = db.get(Doctor, doctor_id)
    if doctor is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not Found")
    context = {
        "doctor": doctor,
        "registered": registered,
        "weekday_label": lambda day: Weekday(day).label,
    }
    return render(request, "doctor.html", context, account=account)
