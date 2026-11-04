"""Development-only command that seeds one staff account for each role.

Usage: APP_ENV=development SEED_PASSWORD=<password> python -m app.seed
"""

import os
import sys

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import Role, StaffAccount

DEV_ACCOUNTS = (
    ("dev.receptionist", Role.RECEPTIONIST),
    ("dev.doctor", Role.DOCTOR),
    ("dev.administrator", Role.ADMINISTRATOR),
)


def seed_staff_accounts(session: Session, password: str) -> list[tuple[str, bool]]:
    """Create missing development accounts; existing accounts are left unchanged.

    Returns each login with True when it was created and False when it already existed.
    """
    existing = set(
        session.scalars(
            select(StaffAccount.login).where(
                StaffAccount.login.in_([login for login, _ in DEV_ACCOUNTS])
            )
        )
    )
    results = []
    for login, role in DEV_ACCOUNTS:
        created = login not in existing
        if created:
            account = StaffAccount(login=login, role=role)
            account.set_password(password)
            session.add(account)
        results.append((login, created))
    return results


def main() -> int:
    if os.environ.get("APP_ENV") != "development":
        print("Refusing to seed: set APP_ENV=development to run this command.", file=sys.stderr)
        return 1
    password = os.environ.get("SEED_PASSWORD")
    if not password:
        print("Refusing to seed: set SEED_PASSWORD for the seeded accounts.", file=sys.stderr)
        return 1

    with Session(get_engine()) as session:
        results = seed_staff_accounts(session, password)
        session.commit()

    for login, created in results:
        print(f"{'created' if created else 'exists '}  {login}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
