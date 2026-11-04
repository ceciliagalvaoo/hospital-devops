import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func, true
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.security import hash_password, verify_password


class Role(enum.StrEnum):
    RECEPTIONIST = "receptionist"
    DOCTOR = "doctor"
    ADMINISTRATOR = "administrator"


class StaffAccount(Base):
    """A hospital staff member who can log in. Patients are not system users."""

    __tablename__ = "staff_accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    login: Mapped[str] = mapped_column(String(64), unique=True)
    password_hash: Mapped[str] = mapped_column(String(60))
    role: Mapped[Role] = mapped_column(
        Enum(
            Role,
            name="staff_role",
            native_enum=False,
            create_constraint=True,
            length=20,
            values_callable=lambda roles: [role.value for role in roles],
        )
    )
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def set_password(self, password: str) -> None:
        """Store only the bcrypt hash of the password, never the plain text."""
        self.password_hash = hash_password(password)

    def check_password(self, password: str) -> bool:
        return verify_password(password, self.password_hash)
