"""Application areas and the roles that may open them (README §3.2 RBAC matrix).

The navigation and the access checks of the area pages both read this table, so a role
never sees a link to an area that would refuse it.
"""

from dataclasses import dataclass

from app.models import Role


@dataclass(frozen=True)
class Area:
    path: str
    title: str
    roles: frozenset[Role]
    description: str
    stories: str


AREAS = (
    Area(
        "/patients",
        "Patients",
        frozenset({Role.RECEPTIONIST, Role.ADMINISTRATOR}),
        "Register, search, edit and deactivate patients.",
        "US-03, US-09, US-10, US-17",
    ),
    Area(
        "/doctors",
        "Doctors",
        frozenset({Role.ADMINISTRATOR}),
        "Register, update and deactivate doctors.",
        "US-02, US-13, US-16",
    ),
    Area(
        "/appointments",
        "Appointments",
        frozenset({Role.RECEPTIONIST, Role.DOCTOR, Role.ADMINISTRATOR}),
        "Schedule, view, update and cancel appointments.",
        "US-04, US-05, US-11, US-12",
    ),
    Area(
        "/records",
        "Medical records",
        frozenset({Role.DOCTOR}),
        "Record consultations, read medical histories and export authorised data.",
        "US-06, US-07, US-08, US-18",
    ),
    Area(
        "/staff",
        "Staff accounts",
        frozenset({Role.ADMINISTRATOR}),
        "Create and deactivate staff accounts.",
        "US-14, US-15",
    ),
)


def areas_for(role: Role) -> list[Area]:
    """Return the areas the role may open, in navigation order."""
    return [area for area in AREAS if role in area.roles]
