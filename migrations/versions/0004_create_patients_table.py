"""Create the patients table.

Administrative patient records (US-03): the name and the date of birth are required, the
phone and e-mail are optional, and patients are deactivated instead of deleted (US-17).
The record number shown to staff is derived from the id, so it needs no column.

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-18
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "patients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("email", sa.String(length=254), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("btrim(full_name) <> ''", name=op.f("ck_patients_full_name_not_blank")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_patients")),
    )


def downgrade() -> None:
    op.drop_table("patients")
