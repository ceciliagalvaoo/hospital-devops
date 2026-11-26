# Test plan

The test plan of `hospital-devops` (Lab 7, Task 6.1, 6.4 and 6.6, #219): which tests verify each user story, where each kind of test runs, the pipeline that runs them, the thresholds and an example of a failed and fixed run. How to run the tests locally is in [development/testing.md](development/testing.md); the test maps and manual checklists of the delivered stories are in [testing/](testing/).

State on 2026-11-26: US-01, US-22, US-23 and US-24 (Sprint 1) and US-02, US-03, US-09, US-10, US-13, US-14 and US-15 (Sprint 2) are delivered and their tests exist; the other stories list the test tasks planned in [tasks.md](tasks.md).

## 1. Test types

| Type | What it verifies | Tool | Where | In CI |
| --- | --- | --- | --- | --- |
| **Unit** | rules without the database or HTTP: password hashing, registration and search rules, availability ranges, image metadata, the workflow contract | pytest | `tests/test_*.py`, `tests/ci/` | `Tests` |
| **Integration** | routes, pages and models together with a real PostgreSQL database, through FastAPI's test client: persistence, validation, HTTP status codes, CSRF, the RBAC matrix | pytest, PostgreSQL 17 | `tests/integration/` | `Tests` |
| **End-to-end (black box)** | the built container image through its public HTTP interface only: start-up, migrations, health, the login journey of every role and the front-desk journey | pytest, Docker Compose | `tests/smoke/` (`-m smoke`) | `Container`, against the image that is published |
| **UI** | the pages in a real browser: navigation, forms, error summaries, focus, small screens | Playwright for Python, headless Chromium | `tests/e2e/` (`-m e2e`) | `E2E` |
| **Published image** | the image pulled anonymously from GHCR: health, login page, non-root user, labels | pytest, Docker Compose | `tests/published/` (`-m published`) | `Verify image`, after `Publish` on `main` |
| **Manual** | what needs human judgement: wording, labels, keyboard use, visible layout | dated checklists | `docs/testing/us-*-manual-checks.md` | — |

Every automated test uses synthetic data only. Commands, from the repository root (details in [development/testing.md](development/testing.md)):

```bash
docker compose --profile test up -d --wait test-db   # the test database
pytest --cov=app                                     # unit and integration, with the coverage gate
pytest -m e2e                                        # UI tests in Chromium
pytest -m smoke                                      # container smoke tests and black-box journeys
PUBLISHED_IMAGE=ghcr.io/ceciliagalvaoo/hospital-devops:sha-<commit> pytest -m published
```

## 2. Test plan per user story

Legend: test files of delivered stories are named; for the other stories the planned test tasks are listed (A = automated, M = manual). **n/a** gives the reason when a type is not used. Two reasons recur:

- **(J)** The black-box journey (`tests/smoke/test_black_box_journey.py`) checks the cross-cutting path through the container (login of each role, the area matrix, logout, register and find a patient). Story-specific behaviour is verified by the integration and UI tests of the story, which run on every pull request; adding every story to the container journey would repeat them more slowly.
- **(R)** The story's rules are short and checked through the routes by its integration tests; a separate unit test is added when a story has a rules module of its own, as US-02, US-03, US-09 and US-10 do.

| Story | Unit | Integration | End-to-end (black box) | UI (browser) | Manual |
| --- | --- | --- | --- | --- | --- |
| **US-01** Login and role-based access | `test_security.py` | `test_auth_sessions.py`, `test_access.py`, `test_csrf.py`, `test_pages.py`, `test_us01_authentication.py` | `test_black_box_journey.py` (every role) | `test_login_navigation.py`, `test_small_screen.py` | [us-01-manual-checks.md](testing/us-01-manual-checks.md) |
| **US-02** Register a doctor | `test_doctor_rules.py` | `test_doctor.py`, `test_doctor_registration.py`, `test_doctor_pages.py`, `test_us02_doctor_registration.py` | n/a (J) | `test_register_and_view_doctor.py` | [us-02-manual-checks.md](testing/us-02-manual-checks.md) |
| **US-03** Register a patient | `test_patient_rules.py` | `test_patient.py`, `test_patient_api.py`, `test_patient_pages.py`, `test_us03_patient_registration.py` | `test_black_box_journey.py` (front desk) | `test_patient_registration.py` | [us-03-manual-checks.md](testing/us-03-manual-checks.md) |
| **US-04** Schedule an appointment | T-04.8 (A): availability and conflict validator | T-04.5 (A) | n/a (J) | T-04.6 (A) | T-04.7 (M) |
| **US-05** View my appointments | n/a (R) | T-05.3 (A) | n/a (J) | T-05.4 (A) | n/a: a read-only list with no form; its wording is covered by the US-04 checks |
| **US-06** Open a patient's record | n/a (R) | T-06.3 (A) | n/a (J) | T-06.4 (A) | n/a: reuses the patient record page checked in US-03 |
| **US-07** Record a consultation | n/a (R) | T-07.4 (A) | n/a (J) | T-07.5 (A) | T-07.6 (M) |
| **US-08** Read previous medical records | n/a (R) | T-08.3 (A) | n/a (J) | T-08.4 (A) | n/a: a read-only history; ordering and access are automated |
| **US-09** Search for a patient | `test_patient_search_rules.py` | `test_patient_search.py`, `test_patient_search_page.py`, `test_us09_patient_search.py` | `test_black_box_journey.py` (front desk) | `test_search_and_open_patient.py` | n/a: the search form uses the labels and messages checked in US-03; the result table was checked at 320 px in #39 |
| **US-10** Edit patient contact details | contact rules in `test_patient_rules.py` | `test_patient_contacts.py`, `test_patient_contacts_page.py`, `test_us10_contact_update.py` | n/a (J) | `test_edit_contacts_and_reload.py` | n/a: the form reuses the fields, messages and summary checked in US-03 |
| **US-11** Update an appointment | n/a: reuses the validator of T-04.8 | T-11.3 (A) | n/a (J) | T-11.4 (A) | n/a: reuses the booking form checked in T-04.7 |
| **US-12** Cancel an appointment | n/a (R) | T-12.3 (A) | n/a (J) | T-12.4 (A) | n/a: a single confirmation action |
| **US-13** Update doctor details | `test_doctor_rules.py` (the rules shared with US-02) | `test_doctor_update.py`, `test_doctor_pages.py`, `test_us13_doctor_update.py` | n/a (J) | `test_edit_doctor_and_reload.py` | n/a: reuses the availability inputs checked in T-02.6 |
| **US-14** Create staff accounts | `test_account_rules.py` | `test_staff_account_creation.py`, `test_staff_pages.py`, `test_us14_staff_account_creation.py` | n/a (J) | `test_create_account_and_log_in.py` | n/a: a short form; login wording is checked in US-01 |
| **US-15** Deactivate a staff account | n/a (R) | `test_staff_account_deactivation.py`, `test_staff_pages.py`, `test_us15_account_deactivation.py` | n/a (J) | `test_deactivate_account_and_refuse_access.py` | n/a: a single action whose effect (refused login) is automated |
| **US-16** Deactivate a doctor | n/a (R) | T-16.3 (A), T-16.4 (A) | n/a (J) | T-16.5 (A) | n/a: a single action |
| **US-17** Deactivate a patient | n/a (R) | T-17.3 (A), T-17.4 (A) | n/a (J) | T-17.5 (A) | n/a: a single action |
| **US-18** Export authorised data | n/a (R) | T-18.3 (A): headers, escaping, empty output | n/a (J) | T-18.4 (A): downloads and checks the CSV | n/a: the CSV content is fully automated |
| **US-19** Filter the appointment calendar | n/a (R) | T-19.3 (A) | n/a (J) | T-19.4 (A) | n/a: filters reuse the calendar page |
| **US-20** Filter my medical records | n/a (R) | T-20.3 (A) | n/a (J) | T-20.4 (A) | n/a: filters reuse the history page |
| **US-21** Filter staff accounts | n/a (R) | T-21.3 (A) | n/a (J) | T-21.4 (A) | n/a: filters reuse the account list |
| **US-22** Containerised application and database | n/a: no application rules; the Dockerfile and Compose file are verified by running them | n/a: the container is verified as a whole by the smoke tests | `test_container.py` (start-up, migrations, health, non-root, failed migration) | n/a: no pages of its own | n/a: fully automated |
| **US-23** Continuous integration and merge checks | `tests/ci/test_ci_workflow.py` (workflow contract) | n/a: the workflow runs on GitHub, not in the test process | n/a: verified by real pipeline runs | n/a: no pages | [us-23-manual-checks.md](testing/us-23-manual-checks.md) (a blocked merge) |
| **US-24** Automated container publication | `test_image_metadata.py` (versions and tags) | n/a: publishing needs the registry | `tests/published/` (the published image, anonymously) | n/a: no pages | [us-24-manual-checks.md](testing/us-24-manual-checks.md) |
| **US-25** Performance and recovery verification | n/a: measures the running system | n/a: needs the running container | T-25.2 (A): load test, 20 users; T-25.4 (A): crash and recovery | n/a: no pages | n/a: results are measured automatically |
| **US-26** Monitoring and metrics dashboard | n/a (R) | T-26.4 (A): metrics updated by requests | n/a (J) | n/a: the dashboard is a monitoring tool, not an application page | T-26.5 (M): refresh, units, labels |

## 3. Pipeline

`.github/workflows/ci.yml` runs on every pull request to `main` and on every push to `main` ([development/ci.md](development/ci.md)):

| Job | Runs | Needs | Required check | Artifacts |
| --- | --- | --- | --- | --- |
| `Lint` | Ruff lint and format check | — | yes | — |
| `Tests` | unit and integration tests with the coverage gate, against a PostgreSQL 17 service container | — | yes | `test-results-tests` (JUnit), `coverage-report` |
| `E2E` | UI tests in headless Chromium against the application and a PostgreSQL service container | — | yes | `test-results-e2e` (JUnit), `playwright-results` (screenshots, videos, traces of failed tests, 14 days) |
| `Container` | builds the image **once**, runs the smoke tests and the black-box journeys against it | — | yes | `test-results-container` (JUnit); on `main`, `tested-image` |
| `Publish` | on `main` only: pushes the tested image without building it | the four checks | — | — |
| `Verify image` | pulls the published image anonymously and checks it | `Publish` | — | — |

The JUnit reports are uploaded with `if: always()`, so they are kept when a test fails. The four checks are the required checks of the ruleset of `main`; a pull request merges only when all four pass on its latest commit ([development/branching-strategy.md](development/branching-strategy.md) §7).

**Why the checks run in parallel instead of a `needs:` chain.** The four checks do not depend on each other: each sets up its own environment. In parallel, a pull request gets every result in the time of the slowest job (`Tests`, 4 min 24 s in run [45818801814](https://github.com/ceciliagalvaoo/hospital-devops/actions/runs/45818801814)) instead of the sum of all four (about 7 min 24 s in that run), and a failure in one job does not hide the results of the others, so one push shows every problem at once. A chain such as `Lint → Tests → E2E → Container` would only save runner minutes on failing runs, at the cost of slower feedback on every run. Only the jobs that must not run without passed checks wait: `Publish` needs all four, and `Verify image` needs `Publish`.

## 4. Thresholds

| Threshold | Value | Where | Justification |
| --- | --- | --- | --- |
| Coverage of `app/` | 100 % of lines **and** branches | `.coveragerc`, the `Tests` job | The application is small and fully covered, so any lower number would let new untested code in unnoticed; branches are included because an untested outcome of a condition is untested logic. Coverage shows what ran, not what was checked, so every task also uses mutation checks ([development/testing.md](development/testing.md), #216). |
| Mutation checks | each new test module must fail when the behaviour it verifies is broken | each task's pull request | A test that passes against a broken application verifies nothing; deliberate faults are introduced and the result is recorded in the pull request. |
| Failed tests | zero; no retries of flaky tests | every job | A retried failure hides a real problem; a flaky test is fixed instead. |
| Load (planned, US-25) | at least 95 % of page requests within two seconds with 20 concurrent users | T-25.2 | NFR-01 ([requirements.md](requirements.md)). |

## 5. A failed and fixed pipeline run

Pull request [#234](https://github.com/ceciliagalvaoo/hospital-devops/pull/234) (#228) changed the `Container` job to run the smoke tests against the already built image (`SMOKE_IMAGE`) instead of building another one.

1. **Failed:** run [44287315809](https://github.com/ceciliagalvaoo/hospital-devops/actions/runs/44287315809), commit `800fe41`. `Lint`, `Tests` and `E2E` passed; `Container` failed with `No such image: postgres:17-alpine`. The local-image mode passed `--pull never` to `docker compose up`, which also applied to the PostgreSQL image, and a clean CI runner does not have it; the local runs had passed only because the image was cached. The merge was blocked by the required check.
2. **Fixed:** commit `6830729` ("fix: pull the database image when smoke-testing a local image") left `pull_policy: never` to the application only, and the fix was reproduced locally after removing the PostgreSQL image. Run [44288215079](https://github.com/ceciliagalvaoo/hospital-devops/actions/runs/44288215079), commit `938373c`, passed all four checks and the pull request was merged.

A deliberate failure is also recorded: run [44298090581](https://github.com/ceciliagalvaoo/hospital-devops/actions/runs/44298090581) of the throw-away pull request #237 failed `Tests` on the coverage gate (a branch no test takes) although all tests passed, which showed that the gate blocks a merge (#216).

## 6. Why a PostgreSQL service container instead of Testcontainers

The integration and UI tests need a real PostgreSQL, because the application relies on PostgreSQL behaviour (check constraints, `btrim`, `ILIKE` with escapes, transactions). Two ways were possible:

- **Service container (chosen).** In CI, GitHub Actions starts `postgres:17-alpine` next to the job, healthy before the tests run; locally, the same image runs as the `test-db` service of Docker Compose (`--profile test`). The tests only read `TEST_DATABASE_URL`. The fixtures refuse a database whose name does not contain `test`, apply all migrations once per session, run each test in a rolled-back transaction and roll the migrations back at the end.
- **Testcontainers.** The tests would start and stop the database themselves through the Docker API.

The service container was chosen because it keeps the `Tests` and `E2E` jobs free of Docker access (only the `Container` job needs Docker), adds no library to the project, starts the database once per job instead of once per test session and process, and uses the same image version in CI and locally. The cost is one manual step locally (`docker compose --profile test up -d --wait test-db`); without it, the integration tests are skipped with instructions, and in CI (`CI=true`) they fail instead of being skipped.
