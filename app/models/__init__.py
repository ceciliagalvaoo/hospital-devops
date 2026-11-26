"""Database models. Import every model module here so Alembic autogenerate can detect it."""

from app.models.doctor import AvailabilityRange, Doctor, Specialisation, Weekday
from app.models.patient import Patient
from app.models.session import StaffSession
from app.models.staff import Role, StaffAccount

__all__ = [
    "AvailabilityRange",
    "Doctor",
    "Patient",
    "Role",
    "Specialisation",
    "StaffAccount",
    "StaffSession",
    "Weekday",
]
