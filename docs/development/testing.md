# Testing and code quality

**Test** the application:

```bash
pytest
```

`pytest` runs the unit, endpoint and integration tests. Integration tests use an isolated PostgreSQL test database, separate from the development database. Start it before running the tests:

```bash
docker compose --profile test up -d --wait test-db
pytest
docker compose --profile test stop test-db
```

The `test-db` service runs only with the `test` profile, uses fixed synthetic credentials, listens on `127.0.0.1:5433` (`TEST_DB_PORT` in `.env`) and keeps its data in memory. Tests connect through `TEST_DATABASE_URL`, which defaults to that service. The fixtures in `tests/conftest.py` refuse a database whose name does not contain `test`, apply all migrations at the start of the session and roll them back at the end, and run each test in a transaction that is rolled back afterwards. Use the `db_session` fixture for database access in tests. When the test database is not running, integration tests are skipped locally with instructions; in CI (`CI=true`) they fail instead.

**Lint and format** the code with Ruff, configured in `ruff.toml`:

```bash
ruff check .            # lint
ruff format .           # format the code
ruff format --check .   # check formatting without changing files
```

**Measure coverage** of the application code, which is also the **coverage gate**:

```bash
pytest --cov=app --cov-report=term-missing
```

`.coveragerc` measures lines **and branches** of `app/` and fails the run below **100 %** ("FAIL Required test coverage of 100.0% not reached"), so the rule is the same locally and in the `Tests` job of CI. Run it on the whole suite with the test database started: a single test file or skipped integration tests cover less and fail the gate. Code that cannot run inside the test process is excluded explicitly with `# pragma: no cover` and justified in its pull request; today the only exclusion is the command-line entry point of `app/seed.py`.

Why 100 %: the application is small (404 statements, 82 branches) and is already fully covered, so any lower threshold would let new untested code in without anyone noticing, while keeping 100 % costs little at this size. Branches are included because a condition whose other outcome is never tested is untested logic even when every line ran. Coverage is necessary, not sufficient: it shows what was executed, not what was checked, so each task also asserts the behaviour and uses mutation checks. The threshold is reviewed in each sprint retrospective (Lab 7, Task 6, #216).

**Test records** are kept in [docs/testing/](../testing): test maps of which automated tests verify each acceptance criterion of a story, and dated manual checklists. US-01: [automated tests](../testing/us-01-automated-tests.md), [manual checks](../testing/us-01-manual-checks.md). US-03: [automated tests](../testing/us-03-automated-tests.md), [manual checks](../testing/us-03-manual-checks.md). US-09: [automated tests](../testing/us-09-automated-tests.md). US-10: [automated tests](../testing/us-10-automated-tests.md). US-23: [manual checks of blocked merges](../testing/us-23-manual-checks.md). US-24: [manual checks of the image publication](../testing/us-24-manual-checks.md).

The published-image checks are marked `published` and excluded by default. They pull an image from the registry instead of building it, start it with PostgreSQL and the migration step through Docker Compose, and check that it reports a working database on `/health`, serves the login page, does not run as root and carries the labels of this repository. `EXPECTED_REVISION` and `EXPECTED_VERSION` additionally compare the commit and version labels:

```bash
PUBLISHED_IMAGE=ghcr.io/ceciliagalvaoo/hospital-devops:sha-<commit> \
EXPECTED_REVISION=<full commit SHA> \
pytest -m published
```

The container smoke tests are marked `smoke` and excluded by default. They require Docker with Docker Compose:

```bash
pytest -m smoke
```

Each smoke run starts an isolated Compose project with settings based on `.env.example` and a free host port. It checks that PostgreSQL becomes healthy, migrations are applied to the latest revision before the application starts, `/health` reports the database status (HTTP 200, and HTTP 503 with the database stopped), the application does not run as root and the application does not start when the migration step fails. The project, its volume and its images are removed afterwards; a local `.env` is not used.

The browser end-to-end tests are marked `e2e` and excluded by default as well. They use Playwright for Python with a headless Chromium and need the test database; install the browser once, then run them:

```bash
python -m playwright install chromium   # once; on a fresh Linux machine add --with-deps
pytest -m e2e
pytest -m e2e --headed --slowmo 500     # watch the browser
```

A pytest fixture starts the application with Uvicorn on a free local port against the test database and creates one synthetic account per role (`e2e.receptionist`, `e2e.doctor`, `e2e.administrator`), which are deleted afterwards. For each role, the tests log in through the login page, check that the navigation shows exactly the areas of the role and that each opens, check that the other areas return "Access denied" with HTTP 403, log out and check that a protected page then shows the login page with HTTP 401. A further test registers a patient through the navigation and the form as a receptionist and as an administrator, checks the error summary and the focus, the saved record with its confirmation and that a reload does not register the patient twice (US-03); another registers two patients, searches by name and by record number, opens the correct record and checks the empty state (US-09); another edits the contact details from the record, with an invalid e-mail first, and reloads the record (US-10); their patients have unique synthetic names and are deleted afterwards. Further tests open every page at a width of 320 px, also with the longest allowed login, and fail if a page scrolls horizontally. When end-to-end and integration tests are selected together, the end-to-end tests run last, because their accounts stay in the database for the whole run.

To inspect a failed end-to-end test, download `playwright-results` from the run's summary page and open the trace of the failed test, which replays each step with the page, network and console:

```bash
python -m playwright show-trace trace.zip
```

The trace can also be opened at <https://trace.playwright.dev> without installing anything; the file stays in the browser.
