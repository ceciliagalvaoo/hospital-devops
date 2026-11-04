"""Create the staff sessions table.

Stores server-side login sessions. Only a SHA-256 hash of the session token is
kept; sessions are removed with their staff account.

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "staff_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("staff_account_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["staff_account_id"],
            ["staff_accounts.id"],
            name=op.f("fk_staff_sessions_staff_account_id_staff_accounts"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_staff_sessions")),
        sa.UniqueConstraint("token_hash", name=op.f("uq_staff_sessions_token_hash")),
    )
    op.create_index(
        op.f("ix_staff_sessions_staff_account_id"),
        "staff_sessions",
        ["staff_account_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_staff_sessions_staff_account_id"), table_name="staff_sessions")
    op.drop_table("staff_sessions")
