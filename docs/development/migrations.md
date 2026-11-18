# Database migrations

**Database migrations** are managed with Alembic. The scripts are in `migrations/versions/`, and `alembic.ini` reads the database URL from `DATABASE_URL`. Run the commands through the `migrate` service so that they use the Compose database:

```bash
docker compose run --rm migrate alembic current            # show the applied revision
docker compose run --rm migrate alembic upgrade head       # apply all pending migrations
docker compose run --rm migrate alembic downgrade -1       # roll back the latest migration
docker compose run --rm migrate alembic history            # list all revisions
```

Revision `0001` is an empty baseline that starts the migration history; revision `0002` creates the `staff_accounts` table, `0003` the `staff_sessions` table and `0004` the `patients` table. Models live in `app/models/` and are registered in `app/models/__init__.py`, which `migrations/env.py` imports. Constraint names follow the naming convention in `app/db.py`, so every migration refers to predictable names. New migrations are created with `alembic revision --autogenerate -m "<description>"` and must be reviewed before they are committed; an integration test fails when the models and the migrations differ.
