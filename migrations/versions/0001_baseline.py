"""Baseline revision with no schema changes.

Marks the starting point of the migration history. Domain tables are added by
later revisions, starting with the staff account model.

Revision ID: 0001
Revises:
Create Date: 2026-11-04
"""

from collections.abc import Sequence

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
