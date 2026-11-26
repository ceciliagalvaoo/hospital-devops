"""Create the doctors and doctor_availability tables.

A doctor profile (US-02) belongs to exactly one staff account, has a name and one
specialisation from a fixed list, and is deactivated instead of deleted (US-16). Its
availability is a set of weekly ranges (weekday, start and end time), removed with the profile.

Revision ID: 0005
Revises: 0004
Create Date: 2026-11-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SPECIALISATIONS = (
    "general_practice",
    "cardiology",
    "dermatology",
    "gynaecology",
    "neurology",
    "orthopaedics",
    "paediatrics",
    "psychiatry",
)


def upgrade() -> None:
    op.create_table(
        "doctors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("staff_account_id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column(
            "specialisation",
            sa.Enum(
                *SPECIALISATIONS,
                name="specialisation",
                native_enum=False,
                create_constraint=True,
                length=40,
            ),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("btrim(full_name) <> ''", name=op.f("ck_doctors_full_name_not_blank")),
        sa.ForeignKeyConstraint(
            ["staff_account_id"],
            ["staff_accounts.id"],
            name=op.f("fk_doctors_staff_account_id_staff_accounts"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_doctors")),
        sa.UniqueConstraint("staff_account_id", name=op.f("uq_doctors_staff_account_id")),
    )
    op.create_table(
        "doctor_availability",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("doctor_id", sa.Integer(), nullable=False),
        sa.Column("weekday", sa.SmallInteger(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.CheckConstraint(
            "weekday BETWEEN 0 AND 6", name=op.f("ck_doctor_availability_weekday_range")
        ),
        sa.CheckConstraint(
            "end_time > start_time", name=op.f("ck_doctor_availability_end_after_start")
        ),
        sa.ForeignKeyConstraint(
            ["doctor_id"],
            ["doctors.id"],
            name=op.f("fk_doctor_availability_doctor_id_doctors"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_doctor_availability")),
    )
    op.create_index(
        op.f("ix_doctor_availability_doctor_id"), "doctor_availability", ["doctor_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_doctor_availability_doctor_id"), table_name="doctor_availability")
    op.drop_table("doctor_availability")
    op.drop_table("doctors")
