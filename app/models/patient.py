from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, String, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

RECORD_NUMBER_PREFIX = "P-"


class Patient(Base):
    """A patient's administrative record. Patients are data, not system users, and the record
    holds no clinical information. Only the name and the date of birth are required (US-03)."""

    __tablename__ = "patients"
    __table_args__ = (CheckConstraint("btrim(full_name) <> ''", name="full_name_not_blank"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    date_of_birth: Mapped[date] = mapped_column(Date)
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(254))
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def record_number(self) -> str:
        """The identifier shown to staff and used by patient search, derived from the id
        assigned by the database, so it is unique and never changes. No national document
        number is collected (data minimisation)."""
        return f"{RECORD_NUMBER_PREFIX}{self.id:06d}"
