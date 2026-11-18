# Task decomposition

## 1. Structure and conventions

The backlog is organised into epics, user stories and implementation tasks.

- An epic groups related stories; it is not estimated separately.
- A user story describes an outcome and receives a story-point estimate.
- A task describes a small, independently reviewable repository change.
- Existing identifiers US-01 to US-21 remain unchanged.
- US-22 to US-26 make the platform and pipeline requirements explicit.
- Task identifiers follow T-XX.Y, where XX identifies the parent story.
- Each task becomes a GitHub Issue titled `T-XX.Y — <short task description>`, worked on a branch named `<issue-number>-<task-id>-<short-description>` and merged through a pull request (see [github-project.md](github-project.md) §7).
- "Blocked by" identifies prerequisites. "None" means no backlog prerequisite.
- Each task has one owner: the project developer, because this is an individual project.
- Each task must have a clear completion condition and should fit into a working session. Larger tasks will be split during refinement.

Implementation will use Python and FastAPI. Database changes will use PostgreSQL migrations. Automated tests will use pytest for unit and integration tests and Playwright for end-to-end tests.

Each task has exactly one classification:
- **Implementation:** a change to application code, configuration, infrastructure or the pipeline.
- **Formal code test — automated:** executable assertions, including unit, integration and end-to-end tests.
- **General test case — manual:** a documented checklist for messages, usability or visual behaviour.
- **Documentation:** a repository change limited to documentation, such as recorded results, commands or limitations.

Every story includes at least one automated test task. Relevant access-control checks are included in the automated tests for protected functionality.

The dependencies below describe implementation order. Completion also requires the shared Definition of Done in [backlog.md](backlog.md) §4, including successful CI checks and container publication. Models and migrations depend on the application and database foundation in US-22, so US-01 is blocked by US-22. US-23 and US-24 are developed alongside US-01 in Sprint 1 to establish the completion checks; only the login end-to-end test links them (T-23.3 is blocked by T-01.7), so no dependency cycle is created.

## 2. Epic overview

| Epic | Name | User stories |
| --- | --- | --- |
| E1 | Authentication and access | US-01, US-14, US-15, US-21 |
| E2 | Patient management | US-03, US-09, US-10, US-17 |
| E3 | Doctor management | US-02, US-13, US-16 |
| E4 | Appointment scheduling | US-04, US-05, US-11, US-12, US-19 |
| E5 | Medical records and export | US-06, US-07, US-08, US-18, US-20 |
| E6 | Platform and pipeline | US-22, US-23, US-24, US-25, US-26 |

## 3. E1 — Authentication and access

### US-01 — Login and role-based access

Blocked by: US-22.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-01.1 | Create the staff account model and migration, with role, active status and bcrypt password hashing | Implementation | T-22.4 |
| T-01.2 | Add a development-only command to seed initial staff accounts for the three roles | Implementation | T-01.1 |
| T-01.3 | Implement login, logout and authenticated session handling | Implementation | T-01.1 |
| T-01.4 | Implement reusable authentication and role checks returning HTTP 401 or 403 | Implementation | T-01.3 |
| T-01.5 | Create the login interface and role-appropriate navigation | Implementation | T-01.4 |
| T-01.6 | Test password hashing, invalid credentials, inactive accounts, sessions, CSRF rejection and allowed/denied role access | Formal code test — automated | T-01.2, T-01.4, T-01.9 |
| T-01.7 | Add Playwright tests for login, protected navigation and logout for each role | Formal code test — automated | T-01.5, T-01.2 |
| T-01.8 | Check login error messages, keyboard navigation and the layout on a small screen | General test case — manual | T-01.5 |
| T-01.9 | Add CSRF protection to state-changing browser requests | Implementation | T-01.3 |

### US-14 — Create staff accounts

Blocked by: US-01.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-14.1 | Implement administrator-only account creation with unique login validation and supported role assignment | Implementation | US-01 |
| T-14.2 | Create the staff account registration form | Implementation | T-14.1 |
| T-14.3 | Test duplicate logins, invalid roles, password hashing and denied access for other roles | Formal code test — automated | T-14.1 |
| T-14.4 | Add an end-to-end test that creates an account and logs in with its assigned role | Formal code test — automated | T-14.2 |

### US-15 — Deactivate a staff account

Blocked by: US-14.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-15.1 | Implement administrator-only deactivation and reject subsequent protected requests from inactive accounts | Implementation | US-14 |
| T-15.2 | Add a deactivation action and confirmation to the staff account interface | Implementation | T-15.1 |
| T-15.3 | Test denied login, rejection of existing sessions after deactivation and role restrictions | Formal code test — automated | T-15.1 |
| T-15.4 | Add an end-to-end test for account deactivation and refused access | Formal code test — automated | T-15.2 |

### US-21 — Filter staff accounts [Extra: Administrator]

Blocked by: US-14, US-15.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-21.1 | Implement an administrator-only account list filtered by role and active status | Implementation | US-14, US-15 |
| T-21.2 | Add role and status controls with an empty-state message | Implementation | T-21.1 |
| T-21.3 | Test individual and combined filters, empty results and denied access | Formal code test — automated | T-21.1 |
| T-21.4 | Add an end-to-end test for changing and clearing filters | Formal code test — automated | T-21.2 |

## 4. E2 — Patient management

### US-03 — Register a patient

Blocked by: US-01.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-03.1 | Create the patient model and migration with name, date of birth, contact details and active status | Implementation | T-22.4 |
| T-03.2 | Implement patient registration with required-field validation and receptionist/administrator permissions | Implementation | T-03.1, US-01 |
| T-03.3 | Create the patient registration form and success confirmation | Implementation | T-03.2 |
| T-03.4 | Test persistence, missing required fields, invalid dates and denied doctor access | Formal code test — automated | T-03.2 |
| T-03.5 | Add an end-to-end test for registration and display of the saved patient | Formal code test — automated | T-03.3 |
| T-03.6 | Check field labels, validation messages and keyboard navigation | General test case — manual | T-03.3 |

The search-specific acceptance criterion in [backlog.md](backlog.md) §3 will be verified when US-09 is integrated. US-03 can be implemented first and demonstrated through the saved patient's detail view.

### US-09 — Search for a patient

Blocked by: US-03.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-09.1 | Implement patient search by name or identifier for receptionists and administrators | Implementation | US-03 |
| T-09.2 | Create the search form, result list and empty state | Implementation | T-09.1 |
| T-09.3 | Test matching results, empty queries, no matches and denied doctor access | Formal code test — automated | T-09.1 |
| T-09.4 | Add an end-to-end test that registers a patient, searches and opens the correct record | Formal code test — automated | T-09.2 |

### US-10 — Edit patient contact details

Blocked by: US-03.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-10.1 | Implement authorised contact updates with input validation | Implementation | US-03 |
| T-10.2 | Create the contact-edit form and save confirmation | Implementation | T-10.1 |
| T-10.3 | Test valid and invalid updates, persistence and denied doctor access | Formal code test — automated | T-10.1 |
| T-10.4 | Add an end-to-end test that edits contacts and reloads the record | Formal code test — automated | T-10.2 |

### US-17 — Deactivate a patient

Blocked by: US-03.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-17.1 | Implement authorised soft deactivation without deleting the patient record | Implementation | US-03 |
| T-17.2 | Add a deactivation confirmation and inactive indicator | Implementation | T-17.1 |
| T-17.3 | Test deactivation, retention of patient data and denied doctor access | Formal code test — automated | T-17.1 |
| T-17.4 | Add integration tests confirming that historical appointments and medical records remain and new bookings are refused | Formal code test — automated | T-17.1, US-04, US-07 |
| T-17.5 | Add an end-to-end test for deactivating a patient | Formal code test — automated | T-17.2 |

Basic deactivation can be implemented before appointments. The history-preservation task is completed after the appointment and medical-record workflows exist.

## 5. E3 — Doctor management

### US-02 — Register a doctor

Blocked by: US-01.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-02.1 | Create doctor and availability models and migrations, including specialisation, active status and staff-account association | Implementation | T-01.1 |
| T-02.2 | Implement administrator-only registration with availability validation | Implementation | T-02.1, US-01 |
| T-02.3 | Create the doctor registration form and availability inputs | Implementation | T-02.2 |
| T-02.4 | Test registration, invalid availability, account association and denied access | Formal code test — automated | T-02.2 |
| T-02.5 | Add an end-to-end test for registering and viewing a doctor | Formal code test — automated | T-02.3 |
| T-02.6 | Check availability input labels and validation wording | General test case — manual | T-02.3 |

Initial doctor accounts are provided by the development seed command. Registering doctor profiles therefore does not depend on the later account-management interface in US-14.

### US-13 — Update doctor details

Blocked by: US-02.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-13.1 | Implement administrator-only updates to doctor details and availability | Implementation | US-02 |
| T-13.2 | Create the doctor-edit form and save confirmation | Implementation | T-13.1 |
| T-13.3 | Test persistence, invalid availability and denied access for other roles | Formal code test — automated | T-13.1 |
| T-13.4 | Add an end-to-end test for updating and reloading doctor details | Formal code test — automated | T-13.2 |

Availability changes apply to new or rescheduled appointments. Existing appointments are retained and are not silently cancelled.

### US-16 — Deactivate a doctor

Blocked by: US-02.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-16.1 | Implement administrator-only soft deactivation while retaining the doctor profile | Implementation | US-02 |
| T-16.2 | Add the deactivation confirmation and inactive indicator | Implementation | T-16.1 |
| T-16.3 | Test profile retention, deactivation and denied access for other roles | Formal code test — automated | T-16.1 |
| T-16.4 | Test retention of historical appointments and refusal of new bookings for inactive doctors | Formal code test — automated | T-16.1, US-04 |
| T-16.5 | Add an end-to-end test for doctor deactivation | Formal code test — automated | T-16.2 |

Doctor profile deactivation prevents new bookings. Staff account deactivation is handled separately by US-15.

## 6. E4 — Appointment scheduling

### US-04 — Schedule an appointment

Blocked by: US-01, US-02, US-03.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-04.1 | Create the appointment model and migration with patient, doctor, datetime, reason and status | Implementation | T-02.1, T-03.1 |
| T-04.2 | Implement the availability and booking-conflict validator | Implementation | T-04.1 |
| T-04.3 | Implement authorised appointment creation with transactional conflict protection and initial scheduled status | Implementation | T-04.2, US-01 |
| T-04.4 | Create the booking form with active patient and doctor selectors | Implementation | T-04.3, US-02, US-03 |
| T-04.5 | Test inactive entities, availability boundaries, duplicate/concurrent bookings and denied doctor access | Formal code test — automated | T-04.3 |
| T-04.6 | Add an end-to-end test for successful booking and refusal of a conflicting booking | Formal code test — automated | T-04.4 |
| T-04.7 | Check conflict messages, missing fields and empty selectors | General test case — manual | T-04.4 |
| T-04.8 | Unit-test the validator for availability boundaries, conflicting slots and cancelled appointments | Formal code test — automated | T-04.2 |

Appointment duration and overlap rules will be documented before implementation. Cancelled appointments do not reserve a slot.

### US-05 — View my appointments

Blocked by: US-04.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-05.1 | Implement an appointment query scoped to the authenticated doctor's profile | Implementation | US-04 |
| T-05.2 | Create the doctor's appointment list with dates and statuses | Implementation | T-05.1 |
| T-05.3 | Test doctor scoping and attempts to access another doctor's appointments | Formal code test — automated | T-05.1 |
| T-05.4 | Add an end-to-end test using two doctors with separate appointment lists | Formal code test — automated | T-05.2 |

### US-11 — Update an appointment

Blocked by: US-04.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-11.1 | Implement authorised appointment updates using the existing availability and conflict rules | Implementation | US-04 |
| T-11.2 | Create the appointment-edit form | Implementation | T-11.1 |
| T-11.3 | Test conflicts, unchanged slots, inactive entities and denied doctor access | Formal code test — automated | T-11.1 |
| T-11.4 | Add an end-to-end test for successful rescheduling and refusal of a conflicting change | Formal code test — automated | T-11.2 |

### US-12 — Cancel an appointment

Blocked by: US-04.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-12.1 | Implement authorised cancellation while retaining the appointment record | Implementation | US-04 |
| T-12.2 | Add the cancellation action, confirmation and status display | Implementation | T-12.1 |
| T-12.3 | Test retained history, slot release, invalid status transitions and denied doctor access | Formal code test — automated | T-12.1 |
| T-12.4 | Add an end-to-end test that cancels an appointment and books the released slot | Formal code test — automated | T-12.2 |

### US-19 — Filter the appointment calendar [Extra: Receptionist]

Blocked by: US-04.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-19.1 | Implement appointment filtering by date and doctor for receptionists and administrators | Implementation | US-04 |
| T-19.2 | Add calendar filters and an empty state | Implementation | T-19.1 |
| T-19.3 | Test individual and combined filters and denied access to the administrative calendar | Formal code test — automated | T-19.1 |
| T-19.4 | Add an end-to-end test for applying and clearing calendar filters | Formal code test — automated | T-19.2 |

## 7. E5 — Medical records and export

### US-06 — Open a patient's record

Blocked by: US-05.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-06.1 | Implement patient-detail access that verifies the authenticated doctor's appointment relationship | Implementation | US-05 |
| T-06.2 | Create the patient-detail view linked from the doctor's appointment list | Implementation | T-06.1 |
| T-06.3 | Test authorised access, unrelated patients and direct requests with altered identifiers | Formal code test — automated | T-06.1 |
| T-06.4 | Add an end-to-end test for opening an assigned patient's record | Formal code test — automated | T-06.2 |

### US-07 — Record a consultation

Blocked by: US-06.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-07.1 | Create the medical-record model and migration linked to an appointment and its doctor | Implementation | T-04.1 |
| T-07.2 | Implement assigned-doctor-only recording of visit date, diagnosis and notes, with an atomic transition to completed | Implementation | T-07.1, US-06 |
| T-07.3 | Create the consultation form and completion confirmation | Implementation | T-07.2 |
| T-07.4 | Test required fields, ownership, duplicate completion, cancelled appointments and atomic persistence | Formal code test — automated | T-07.2 |
| T-07.5 | Add an end-to-end test for recording a consultation and verifying completed status | Formal code test — automated | T-07.3 |
| T-07.6 | Check clinical field labels and validation messages | General test case — manual | T-07.3 |

### US-08 — Read previous medical records

Blocked by: US-07.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-08.1 | Implement medical-history retrieval for the authenticated doctor's authorised patients | Implementation | US-07 |
| T-08.2 | Create the chronological history view and empty state | Implementation | T-08.1 |
| T-08.3 | Test ordering, empty histories and denial for receptionists, administrators and unrelated doctors | Formal code test — automated | T-08.1 |
| T-08.4 | Add an end-to-end test that records a consultation and reads it in the patient's history | Formal code test — automated | T-08.2 |

### US-18 — Export authorised data

Blocked by: US-08.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-18.1 | Implement a doctor-only CSV export reusing the authorised-patient scope and documenting exported columns | Implementation | US-08 |
| T-18.2 | Add the export action and download response | Implementation | T-18.1 |
| T-18.3 | Test authorisation, excluded records, headers, escaping, empty output and spreadsheet-formula input handling | Formal code test — automated | T-18.1 |
| T-18.4 | Add an end-to-end test that downloads a CSV and verifies its authorised contents | Formal code test — automated | T-18.2 |

### US-20 — Filter my medical records [Extra: Doctor]

Blocked by: US-08.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-20.1 | Add visit-date filtering to the authorised medical-history query | Implementation | US-08 |
| T-20.2 | Add date controls and an empty state to the history view | Implementation | T-20.1 |
| T-20.3 | Test date boundaries, invalid ranges and preservation of the authorised-patient scope | Formal code test — automated | T-20.1 |
| T-20.4 | Add an end-to-end test for filtering and clearing the date range | Formal code test — automated | T-20.2 |

## 8. E6 — Platform and pipeline

The following stories are part of the Product Backlog in [backlog.md](backlog.md) §1, with acceptance criteria in [backlog.md](backlog.md) §3. They represent the non-functional and delivery work already described in the Lab 1 requirements and sprint outline.

### US-22 — Containerised application and database

As a developer, I want to run the application and database through a documented container setup, so that development and delivery use a reproducible environment.

Blocked by: None.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-22.1 | Create the minimal FastAPI application structure and health endpoint | Implementation | None |
| T-22.2 | Create the application Dockerfile with a non-root runtime user | Implementation | T-22.1 |
| T-22.3 | Configure Docker Compose for the application and PostgreSQL, including persistence and environment configuration | Implementation | T-22.2 |
| T-22.4 | Add and document database migration and startup commands | Implementation | T-22.3 |
| T-22.5 | Automate a container smoke check for startup, health and database connectivity | Formal code test — automated | T-22.4 |

### US-23 — Continuous integration and merge checks

As a developer, I want pull requests to run automated checks, so that failing changes are identified before merging.

Blocked by: US-22.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-23.1 | Configure pytest fixtures and an isolated PostgreSQL test database | Implementation | US-22 |
| T-23.2 | Add a GitHub Actions workflow for Ruff linting and unit/integration tests with pytest-cov coverage reporting | Implementation | T-23.1 |
| T-23.3 | Add headless Playwright execution and failure artifacts to CI | Implementation | T-23.2, T-01.7 |
| T-23.4 | Configure required checks and document the pull-request branching workflow | Implementation | T-23.3, T-23.7 |
| T-23.5 | Add a CI smoke test and verify that a deliberately failing test produces a failed required check | Formal code test — automated | T-23.2 |
| T-23.6 | Verify with a test pull request that failed required checks prevent merging | General test case — manual | T-23.4, T-23.5 |
| T-23.7 | Add the container image build to the pull-request workflow | Implementation | T-23.2 |

The login end-to-end test is introduced alongside US-01. Pipeline completion requires it, but implementing login does not depend on the pipeline already being complete.

### US-24 — Automated container publication

As a developer, I want successful changes on main to publish a traceable container image to GHCR, so that each delivered image can be linked to its source commit.

Blocked by: US-23.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-24.1 | Configure main-branch image publication after successful automated checks | Implementation | US-23 |
| T-24.2 | Add commit-SHA image tags, source metadata and documentation of the versioning scheme | Implementation | T-24.1 |
| T-24.3 | Automate a smoke check that pulls the published image and verifies its health endpoint | Formal code test — automated | T-24.2 |
| T-24.4 | Check that pull requests cannot publish release images and that the published SHA matches its source commit | General test case — manual | T-24.3 |

This story covers automated image delivery. Publication to GHCR is not presented as deployment to a running production environment.

### US-25 — Performance and recovery verification

As a maintainer, I want repeatable performance and recovery checks, so that the application can demonstrate the response-time and restart requirements.

Blocked by: US-22, US-04.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-25.1 | Create a reproducible demo dataset and authenticated load-test scenarios | Implementation | US-04 |
| T-25.2 | Add a load test for 20 concurrent users asserting that at least 95% of page requests finish within two seconds | Formal code test — automated | T-25.1 |
| T-25.3 | Configure and document the application container restart policy | Implementation | US-22 |
| T-25.4 | Automate an application-process crash and verify recovery within 30 seconds | Formal code test — automated | T-25.3 |
| T-25.5 | Document test environment, commands, results and any limitations | Documentation | T-25.2, T-25.4 |

### US-26 — Monitoring and metrics dashboard

As a maintainer, I want application and container metrics on a dashboard, so that I can observe errors, response times and resource usage.

Blocked by: US-22.

| ID | Task | Classification | Blocked by |
| --- | --- | --- | --- |
| T-26.1 | Instrument request counts, error counts and response-time metrics | Implementation | US-22 |
| T-26.2 | Configure Prometheus and a container-metrics collector | Implementation | T-26.1 |
| T-26.3 | Provision a Grafana dashboard for request rate, error rate, response times, CPU and memory, refreshing within 30 seconds | Implementation | T-26.2 |
| T-26.4 | Automate checks that requests update application metrics and monitoring targets expose the expected series | Formal code test — automated | T-26.2 |
| T-26.5 | Verify dashboard refresh, units, labels and visible changes after generated traffic | General test case — manual | T-26.3, T-26.4 |

## 9. Refinement and completion

The decomposition is an initial implementation plan. Tasks will be refined before their story enters a sprint.

- Dependencies must be checked before selecting work.
- A task that takes more than a working session will be split.
- Additional test cases will be added when implementation reveals new boundaries or risks.
- Cross-story verification tasks must be completed before the parent story is counted as done.
- Optional stories US-19 to US-21 are selected only if capacity remains after required work.
- A story is complete only when its acceptance criteria and the Definition of Done are satisfied.
- Story points include implementation, testing and review; test tasks are not added again as separate story-point estimates.
