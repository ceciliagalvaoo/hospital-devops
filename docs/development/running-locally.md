# Running locally

The application requires Python 3.12 or later. Commands are run from the repository root.

**Install** the application and test dependencies in a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1      # Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
```

`requirements.txt` holds the runtime dependencies; `requirements-dev.txt` adds the test tools.

**Run** the application:

```bash
uvicorn app.main:app --reload
```

The health endpoint is available at <http://127.0.0.1:8000/health>. It returns HTTP 200 and `{"status": "ok", "database": "ok"}` when the PostgreSQL database configured in `DATABASE_URL` is reachable, and HTTP 503 and `{"status": "error", "database": "unavailable"}` otherwise. Without a database, run the complete stack with Docker Compose as described below. The interactive API documentation (`/docs`, `/redoc` and `/openapi.json`) is served only when `APP_ENV=development`, as set in `.env.example`, for example at <http://127.0.0.1:8000/docs>. Without that setting, including in the published image, these paths return HTTP 404, so the endpoints are not listed to anonymous visitors (#225).

**Run in a container** (requires Docker):

```bash
docker build -t hospital-devops .
docker run --rm -p 8000:8000 hospital-devops
```

The image is a multi-stage build based on `python:3.13.18-slim`: a build stage installs the runtime dependencies from `requirements.txt` into a virtual environment, and the runtime stage contains only that environment and the application files, runs as the unprivileged user `app` (UID 10001) and carries the `org.opencontainers.image.*` labels. The health endpoint is available at the same address as above; without a database it reports HTTP 503. Build arguments, tagging, the stage structure, measurements and the choice of base image are documented in [docs/docker-build.md](../docker-build.md).

**Run with PostgreSQL** using Docker Compose:

```powershell
Copy-Item .env.example .env       # Linux/macOS: cp .env.example .env
docker compose up --build
```

Compose starts PostgreSQL 17, applies pending database migrations through the one-off `migrate` service and then starts the application. Migrations run only after the database health check passes, and the application starts only after the migrations finish successfully. Both services receive the connection settings through `DATABASE_URL`. Settings are read from `.env`, which is ignored by Git; Compose stops with an error if a required setting is missing. Database data is kept in the named volume `db-data`, so it survives `docker compose down`. To also remove the data, run `docker compose down -v`.

**Seed development accounts** for the three roles after the stack is running:

```bash
docker compose run --rm app python -m app.seed
```

The command creates the active accounts `dev.receptionist`, `dev.doctor` and `dev.administrator`, all with the password from `SEED_PASSWORD` in `.env`. Running it again leaves existing accounts and their passwords unchanged. It is development-only: it refuses to run unless `APP_ENV=development` (Compose defaults to `production` when the setting is missing) and refuses to run without `SEED_PASSWORD`. If your `.env` was created before these settings existed, add `APP_ENV`, `SEED_PASSWORD` and `SESSION_COOKIE_SECURE` from `.env.example`.

**Use the application in a browser** at <http://127.0.0.1:8000/login> after seeding the development accounts. The pages are server-rendered with Jinja2 (`app/templates/`, styles in `app/static/`):

| Page | Behaviour |
| --- | --- |
| `/login` | Login form. Valid credentials redirect to the home page; wrong passwords, unknown logins and inactive accounts see the same message with HTTP 401. |
| `/` | Home page with the logged-in account, its role and the areas of that role. |
| `/patients`, `/doctors`, `/appointments`, `/records`, `/staff` | Areas of the application. They are placeholders until the stories that deliver them (see the table below), but already enforce the role checks. |
| Log out button | Ends the session (`POST /logout`) and returns to the login page. |

The navigation shows each role only the areas allowed by the RBAC matrix ([requirements.md](../requirements.md) §2.2); `app/navigation.py` holds this table and is used both for the links and for the access checks of the area pages:

| Area | Receptionist | Doctor | Administrator | Delivered by |
| --- | --- | --- | --- | --- |
| Patients | Yes | No | Yes | US-03, US-09, US-10, US-17 |
| Doctors | No | No | Yes | US-02, US-13, US-16 |
| Appointments | Yes | Yes | Yes | US-04, US-05, US-11, US-12 |
| Medical records | No | Yes | No | US-06, US-07, US-08, US-18 |
| Staff accounts | No | No | Yes | US-14, US-15 |

Pages keep the status codes of NFR-04: a page opened without a valid session returns the login page with HTTP 401, and an area of another role returns an "Access denied" page with HTTP 403. Requests whose `Accept` header does not include `text/html`, such as `curl` or API clients, still receive the JSON responses described in [authentication.md](authentication.md).
