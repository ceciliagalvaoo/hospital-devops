"""Database models. Import every model module here so Alembic autogenerate can detect it."""

from app.models.staff import Role, StaffAccount

__all__ = ["Role", "StaffAccount"]
