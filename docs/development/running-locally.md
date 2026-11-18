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
| `/patients` | Patients area (US-09), for receptionists and administrators: a link to register a patient and the search by name or record number. Results list the record number, the name (linked to the record), the date of birth and the status, ordered by name, at most 50 with a notice when there are more; a search without matches shows an empty-state message with a link to register the patient; an empty or one-character query shows its message next to the field with HTTP 422. On small screens the table scrolls inside its own keyboard-focusable region. |
| `/doctors`, `/appointments`, `/records`, `/staff` | Areas of the application. They are placeholders until the stories that deliver them (see the table below), but already enforce the role checks. |
| `/patients/new` | Patient registration form (US-03), for receptionists and administrators. Invalid data returns the form with HTTP 422, the entered values, a summary of the errors linked to the fields and a message next to each invalid field; the focus moves to the first invalid field. A valid patient is saved and the browser is redirected to the record. |
| `/patients/<id>` | The patient's record: record number, date of birth, phone, e-mail and status, with a confirmation after registration or after saving contact details, and a link to edit the contact details. Unknown records return "Page not found" with HTTP 404. |
| `/patients/<id>/contacts` | Contact-edit form (US-10), for receptionists and administrators, filled in with the current phone and e-mail; an empty field removes that contact. Invalid data returns the form with HTTP 422, the entered values, the error summary and the field messages, with the focus on the first invalid field; saving redirects to the record with "Contact details saved.". |
| Log out button | Ends the session (`POST /logout`) and returns to the login page. |

The navigation shows each role only the areas allowed by the RBAC matrix ([requirements.md](../requirements.md) §2.2); `app/navigation.py` holds this table and is used both for the links and for the access checks of the area pages:

| Area | Receptionist | Doctor | Administrator | Delivered by |
| --- | --- | --- | --- | --- |
| Patients | Yes | No | Yes | US-03, US-09, US-10, US-17 |
| Doctors | No | No | Yes | US-02, US-13, US-16 |
| Appointments | Yes | Yes | Yes | US-04, US-05, US-11, US-12 |
| Medical records | No | Yes | No | US-06, US-07, US-08, US-18 |
| Staff accounts | No | No | Yes | US-14, US-15 |

**Register a patient** through the API (US-03), with the same rules as the `/patients/new` page. Only receptionists and administrators may register patients; doctors receive HTTP 403 and requests without a session HTTP 401:

| Endpoint | Behaviour |
| --- | --- |
| `POST /api/patients` | Form fields `full_name`, `date_of_birth` (`YYYY-MM-DD`), `phone` and `email`. Returns HTTP 201 with the saved patient and its record number (`P-000001`), or HTTP 422 with `{"detail": "Invalid patient data.", "errors": {...}}`, a message for every invalid field. |
| `GET /api/patients?q=…` | Searches patients (US-09) by record number (`P-000042`, `P42` or `42`) or by words of the name: every word must appear in the name, in any order and ignoring case (`silva maria` finds "Maria da Silva"). Returns `{"patients": [...], "more": false}`, ordered by name, at most 50 patients, with `more` set when there are further matches; active and inactive patients are listed. An empty query, or a name query of one character, returns HTTP 422 with the message to show. |
| `POST /api/patients/<id>/contacts` | Replaces the phone and e-mail of a patient (US-10), with the same format rules as registration; a blank field removes that contact. Returns HTTP 200 with the updated patient, HTTP 422 with a message for every invalid field (nothing is changed), and HTTP 404 for an unknown patient. |

Search does not ignore accents yet: "Cecilia" does not find "Cecília". Ignoring them needs the PostgreSQL `unaccent` extension and is left as a later improvement; until then, search with part of the name that has no accent. The registration rules are in `app/patients.py` and apply to the API and the pages alike: the name (at most 120 characters) and a real date of birth between 1900-01-01 and today are required; the phone (8 to 15 digits, optionally with `+`, spaces, brackets and hyphens) and the e-mail are optional but must be well formed when given. With `curl`, send the fields with `--data-urlencode`, because a plain `-d` turns the `+` of a phone number into a space (the session cookie and the `token` function are those of the login example in [authentication.md](authentication.md)):

```bash
curl -b cookies.txt -c cookies.txt -H "X-CSRF-Token: $(token)" "$URL/api/patients" \
  --data-urlencode "full_name=Synthetic Patient" --data-urlencode date_of_birth=1990-05-17 \
  --data-urlencode "phone=+55 11 90000-0000" --data-urlencode email=patient@example.test
```

Pages keep the status codes of NFR-04: a page opened without a valid session returns the login page with HTTP 401, and an area of another role returns an "Access denied" page with HTTP 403. Requests whose `Accept` header does not include `text/html`, such as `curl` or API clients, still receive the JSON responses described in [authentication.md](authentication.md).
