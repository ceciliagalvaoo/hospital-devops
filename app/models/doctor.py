import enum
from datetime import datetime, time

from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, SmallInteger, String, Time, func
from sqlalchemy import true as sql_true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.staff import StaffAccount


class Specialisation(enum.StrEnum):
    """The fixed list of specialisations, chosen by the Product Owner (US-02, 2026-11-26)."""

    GENERAL_PRACTICE = "general_practice"
    CARDIOLOGY = "cardiology"
    DERMATOLOGY = "dermatology"
    GYNAECOLOGY = "gynaecology"
    NEUROLOGY = "neurology"
    ORTHOPAEDICS = "orthopaedics"
    PAEDIATRICS = "paediatrics"
    PSYCHIATRY = "psychiatry"

    @property
    def label(self) -> str:
        return self.value.replace("_", " ").capitalize()


class Weekday(enum.IntEnum):
    """Days of a weekly availability range; Monday is 0, as in ``date.weekday()``."""

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6

    @property
    def label(self) -> str:
        return self.name.capitalize()


class Doctor(Base):
    """A doctor's profile: the name, specialisation and weekly availability of a staff account
    with the doctor role. Doctors are deactivated instead of deleted (US-16)."""

    __tablename__ = "doctors"
    __table_args__ = (CheckConstraint("btrim(full_name) <> ''", name="full_name_not_blank"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    staff_account_id: Mapped[int] = mapped_column(
        ForeignKey("staff_accounts.id", ondelete="RESTRICT"), unique=True
    )
    full_name: Mapped[str] = mapped_column(String(120))
    specialisation: Mapped[Specialisation] = mapped_column(
        Enum(
            Specialisation,
            name="specialisation",
            native_enum=False,
            create_constraint=True,
            length=40,
            values_callable=lambda values: [value.value for value in values],
        )
    )
    is_active: Mapped[bool] = mapped_column(default=True, server_default=sql_true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    account: Mapped[StaffAccount] = relationship()
    availability: Mapped[list["AvailabilityRange"]] = relationship(
        back_populates="doctor",
        cascade="all, delete-orphan",
        order_by="(AvailabilityRange.weekday, AvailabilityRange.start_time)",
    )


class AvailabilityRange(Base):
    """A time range in which a doctor works every week, for example Monday 08:00-12:00.
    The database keeps each range well formed; overlaps and the 30-minute grid are checked
    by the registration rules."""

    __tablename__ = "doctor_availability"
    __table_args__ = (
        CheckConstraint("weekday BETWEEN 0 AND 6", name="weekday_range"),
        CheckConstraint("end_time > start_time", name="end_after_start"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="CASCADE"), index=True)
    weekday: Mapped[int] = mapped_column(SmallInteger)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)

    doctor: Mapped[Doctor] = relationship(back_populates="availability")
