# Product backlog

## 1. Ordered user stories

The following list is ordered by implementation priority, considering
dependencies, risk and business value. Story identifiers remain stable
if the backlog is reordered.

1. **US-22 — Containerised application and database**
   As a developer, I want to run the application and database through
   a documented container setup, so that development and delivery use
   a reproducible environment.

2. **US-01 — Login and role-based access**
   As a receptionist, doctor or administrator, I want to log in and
   access only the functionality permitted for my role, so that
   hospital information is protected against unauthorised access.

3. **US-23 — Continuous integration and merge checks**
   As a developer, I want pull requests to run automated checks, so
   that failing changes are identified before merging.

4. **US-24 — Automated container publication**
   As a developer, I want successful changes on main to publish a
   traceable container image to GHCR, so that each delivered image can
   be linked to its source commit.

5. **US-02 — Register a doctor**
   As an administrator, I want to register a doctor with their
   specialisation and availability, so that receptionists can assign
   appointments to an appropriate available doctor.

6. **US-03 — Register a patient**
   As a receptionist, I want to register a patient with their name,
   date of birth and contact details, so that the patient can be
   booked for an appointment.

7. **US-04 — Schedule an appointment**
   As a receptionist, I want to schedule an appointment with a
   patient, doctor, date, time and reason without double-booking, so
   that patients receive a confirmed consultation slot.

8. **US-05 — View my appointments**
   As a doctor, I want to view my scheduled appointments, so that I
   can prepare for upcoming consultations.

9. **US-06 — Open a patient's record**
   As a doctor, I want to open the record of a patient assigned to my
   appointment, so that I can identify the patient correctly before
   providing care.

10. **US-07 — Record a consultation**
    As a doctor, I want to record the visit date, diagnosis and notes
    and mark the appointment as completed, so that future care can
    rely on documented consultation outcomes.

11. **US-08 — Read previous medical records**
    As a doctor, I want to read previous medical records of my
    authorised patients, so that I can make informed clinical
    decisions.

12. **US-09 — Search for a patient**
    As a receptionist, I want to search for an existing patient, so
    that I can locate the correct record without creating duplicates.

13. **US-10 — Edit patient contact details**
    As a receptionist, I want to update a patient's contact details,
    so that the hospital can reach them using current information.

14. **US-11 — Update an appointment**
    As a receptionist, I want to change appointment details while
    respecting doctor availability and preventing double-booking, so
    that changes in patient needs can be accommodated.

15. **US-12 — Cancel an appointment**
    As a receptionist, I want to cancel an appointment while retaining
    its record, so that the slot becomes available and the hospital
    preserves the scheduling history.

16. **US-13 — Update doctor details**
    As an administrator, I want to update a doctor's details and
    availability, so that appointment scheduling uses accurate
    information.

17. **US-14 — Create staff accounts**
    As an administrator, I want to create a staff account and assign
    one of the three supported roles, so that new staff members
    receive appropriate system access.

18. **US-15 — Deactivate a staff account**
    As an administrator, I want to deactivate a staff account, so that
    former staff members can no longer access hospital information.

19. **US-16 — Deactivate a doctor**
    As an administrator, I want to deactivate an unavailable doctor
    while preserving past appointments, so that new appointments
    cannot be assigned to that doctor and historical information
    remains.

20. **US-17 — Deactivate a patient**
    As a receptionist, I want to deactivate a patient record while
    preserving past appointments and medical records, so that inactive
    patients are excluded from new bookings without losing their
    history.

21. **US-18 — Export authorised data**
    As a doctor, I want to export my authorised data as a CSV report,
    so that I can analyse consultation information outside the
    application.

22. **US-25 — Performance and recovery verification**
    As a maintainer, I want repeatable performance and recovery
    checks, so that the application can demonstrate the response-time
    and restart requirements.

23. **US-26 — Monitoring and metrics dashboard**
    As a maintainer, I want application and container metrics on a
    dashboard, so that I can observe errors, response times and
    resource usage.

24. **US-19 — Filter the appointment calendar [Extra: Receptionist]**
    As a receptionist, I want to filter appointments by date and
    doctor, so that I can answer scheduling questions more quickly.

25. **US-20 — Filter my medical records [Extra: Doctor]**
    As a doctor, I want to filter my authorised patients' medical
    records by visit date, so that I can find relevant consultations
    efficiently during follow-up care.

26. **US-21 — Filter staff accounts [Extra: Administrator]**
    As an administrator, I want to filter staff accounts by role and
    active status, so that I can review access assignments
    efficiently.

## 2. Prioritisation rationale

Among the functional stories, login and role-based access come first
because every protected workflow depends on identifying staff and
enforcing permissions.
Doctor registration and patient registration follow because
both are prerequisites for scheduling, with doctor availability
establishing the scheduling constraints before bookings are introduced.

The platform stories US-22 to US-26 make the delivery and non-functional
requirements explicit backlog items. US-22 comes first because every
story needs the application, database and migration foundation.
US-23 and US-24 follow login so that the Definition of Done checks
exist from Sprint 1. US-25 and US-26 are placed after the functional
workflows they measure, and the extra stories US-19 to US-21 come last.

## 3. Acceptance criteria

### US-01 — Login and role-based access

- Given an active staff account with valid credentials, when the staff
  member logs in, then the system grants access according to their role.
- Given invalid credentials or an inactive account, when login is
  attempted, then access is refused.
- Given an unauthenticated request to a protected route, when the
  request is processed, then the system returns HTTP 401.
- Given an authenticated staff member without the required permission,
  when they request a restricted action, then the system returns HTTP 403.

### US-02 — Register a doctor

- Given an authenticated administrator and valid doctor details,
  specialisation and availability, when registration is submitted, then
  the doctor is saved as active and linked to a doctor staff account.
- Given missing required details or invalid availability, when
  registration is submitted, then the system rejects it and identifies
  the invalid fields.
- Given a receptionist or doctor, when they attempt to register a
  doctor, then the system refuses the action.

### US-03 — Register a patient

- Given an authenticated receptionist and valid patient information,
  when registration is submitted, then the patient is saved and
  can be found through patient search.
- Given a missing required name or date of birth, when registration
  is submitted, then the system rejects it and identifies the missing fields.
- Given an authenticated doctor, when they attempt to register a
  patient, then the system refuses the action.

### US-04 — Schedule an appointment

- Given an active patient, an active doctor and an available slot,
  when a receptionist submits all required appointment details,
  then the system creates an appointment with status "scheduled".
- Given a doctor already has a scheduled appointment at a particular
  date and time, when another booking is attempted for that same
  doctor and slot, then the system rejects it and explains the conflict.
- Given an inactive patient, an inactive doctor or a slot outside
  the doctor's availability, when booking is attempted, then
  the system rejects the appointment.

### US-05 — View my appointments

- Given an authenticated doctor, when they open their appointment list,
  then only appointments assigned to them are shown with their date,
  time and status.
- Given a doctor, when they request another doctor's appointment,
  including through a direct request, then the system refuses the
  action.

### US-06 — Open a patient's record

- Given a doctor with an appointment for a patient, when they open that
  patient's record from the appointment, then the patient's details are
  displayed.
- Given a doctor without an appointment relationship to a patient, when
  they request that patient's record, including with an altered
  identifier, then the system refuses the action.

### US-07 — Record a consultation

- Given a doctor assigned to a scheduled appointment, when they
  submit a visit date, diagnosis and notes and complete the consultation,
  then the system saves the medical record and marks the appointment
  as "completed".
- Given a receptionist, administrator or an unassigned doctor,
  when they attempt to record clinical information for that appointment,
  then the system refuses the action.
- Given a saved medical record, when an authorised doctor opens
  the patient's history, then the consultation information is displayed.

### US-08 — Read previous medical records

- Given a doctor authorised for a patient, when they open the patient's
  medical history, then previous records are displayed in chronological
  order.
- Given an authorised patient without medical records, when the history
  is opened, then an empty-state message is displayed.
- Given a receptionist, administrator or unrelated doctor, when they
  request the medical history, then the system refuses the action.

### US-09 — Search for a patient

- Given an authenticated receptionist or administrator, when they search
  by patient name or identifier, then matching patients are listed.
- Given a search without matches, when it is submitted, then an empty-
  state message is displayed.
- Given an authenticated doctor, when they attempt to use patient
  search, then the system refuses the action.

### US-10 — Edit patient contact details

- Given a receptionist or administrator and valid contact details, when
  the changes are saved, then the updated details are persisted and
  displayed after reloading the record.
- Given invalid contact details, when the changes are submitted, then
  the system rejects them and identifies the invalid fields.
- Given an authenticated doctor, when they attempt to edit patient
  contact details, then the system refuses the action.

### US-11 — Update an appointment

- Given a scheduled appointment and a new slot within the doctor's
  availability without a conflict, when a receptionist or administrator
  saves the change, then the appointment is updated.
- Given a conflicting slot, a slot outside the doctor's availability, or
  an inactive patient or doctor, when the change is submitted, then the
  system rejects it and explains the reason.
- Given an appointment saved without changing its slot, when the update
  is processed, then the appointment is not treated as conflicting with
  itself.
- Given an authenticated doctor, when they attempt to update an
  appointment, then the system refuses the action.

### US-12 — Cancel an appointment

- Given a scheduled appointment, when a receptionist or administrator
  cancels it, then its status becomes "cancelled" and the record is
  retained.
- Given a cancelled appointment, when a new booking is submitted for the
  same doctor and slot, then the booking can be accepted.
- Given a completed or already cancelled appointment, when cancellation
  is attempted, then the system rejects the status change.
- Given an authenticated doctor, when they attempt to cancel an
  appointment, then the system refuses the action.

### US-13 — Update doctor details

- Given an authenticated administrator and valid changes, when doctor
  details or availability are saved, then the changes are persisted and
  existing appointments are retained.
- Given invalid availability, when the change is submitted, then the
  system rejects it and identifies the invalid fields.
- Given a receptionist or doctor, when they attempt to update doctor
  details, then the system refuses the action.

### US-14 — Create staff accounts

- Given an authenticated administrator, a unique login and one of the
  three supported roles, when the account is created, then the password
  is stored as a bcrypt hash and the new user can log in with the
  assigned role.
- Given a duplicate login or an unsupported role, when account creation
  is submitted, then the system rejects it.
- Given a receptionist or doctor, when they attempt to create a staff
  account, then the system refuses the action.

### US-15 — Deactivate a staff account

- Given an active staff account, when an administrator deactivates it,
  then later login attempts are refused and requests through existing
  sessions are rejected.
- Given a receptionist or doctor, when they attempt to deactivate a
  staff account, then the system refuses the action.

### US-16 — Deactivate a doctor

- Given an active doctor, when an administrator deactivates the doctor,
  then the profile and historical appointments are retained and new
  bookings for that doctor are refused.
- Given a receptionist or doctor, when they attempt to deactivate a
  doctor, then the system refuses the action.

### US-17 — Deactivate a patient

- Given an active patient, when a receptionist or administrator
  deactivates the patient, then the patient record, historical
  appointments and medical records are retained and new bookings are
  refused.
- Given an authenticated doctor, when they attempt to deactivate a
  patient, then the system refuses the action.

### US-18 — Export authorised data

- Given an authenticated doctor, when they export data, then the CSV
  file contains only authorised data for their own patients, using the
  documented columns.
- Given exported values that begin with spreadsheet-formula characters,
  when the CSV file is generated, then those values are neutralised.
- Given a receptionist or administrator, when they attempt an export,
  then the system refuses the action.

### US-19 — Filter the appointment calendar [Extra: Receptionist]

- Given a receptionist or administrator, when they filter appointments
  by date, doctor or both, then only matching appointments are
  displayed, and clearing the filters restores the full list.
- Given filters without matching appointments, when they are applied,
  then an empty-state message is displayed.
- Given an authenticated doctor, when they request the administrative
  calendar, then the system refuses the action.

### US-20 — Filter my medical records [Extra: Doctor]

- Given an authenticated doctor and a valid visit-date range, when the
  filter is applied, then only authorised records within that range are
  displayed.
- Given a start date later than the end date, when the filter is
  applied, then the system rejects the range.
- Given any filter, when results are returned, then records outside the
  doctor's authorised patients are never included.

### US-21 — Filter staff accounts [Extra: Administrator]

- Given an authenticated administrator, when they filter accounts by
  role, active status or both, then only matching accounts are
  displayed.
- Given filters without matching accounts, when they are applied, then
  an empty-state message is displayed.
- Given a receptionist or doctor, when they request the account list,
  then the system refuses the action.

### US-22 — Containerised application and database

- Given a fresh clone and settings based on `.env.example`, when the
  documented start command is run, then the application and PostgreSQL
  start, migrations are applied and the health endpoint reports a
  working database connection.
- Given the application container, when it is running, then the
  application process does not run as root.

### US-23 — Continuous integration and merge checks

- Given a pull request, when it is opened or updated, then CI runs
  linting, unit, integration and end-to-end tests and a container build.
- Given a failing required check, when a merge is attempted, then GitHub
  prevents the merge.

### US-24 — Automated container publication

- Given a change merged into main that passes the required checks, when
  the pipeline completes, then an image tagged with the commit SHA is
  published to GHCR.
- Given a pull request, when its workflow runs, then no release image is
  published.
- Given a published image, when it is pulled and started, then its
  health endpoint responds successfully.

### US-25 — Performance and recovery verification

- Given the seeded demo dataset and 20 concurrent authenticated users,
  when the load test runs, then at least 95% of page requests complete
  within two seconds.
- Given a running application container, when the application process
  crashes, then the container restarts automatically and is healthy
  again within 30 seconds.

### US-26 — Monitoring and metrics dashboard

- Given the running stack, when the dashboard is opened, then request
  counts, error rates, response times and container CPU and memory usage
  are displayed, refreshing at least every 30 seconds.
- Given generated traffic, when the dashboard refreshes, then the change
  is visible in the request metrics.
- Given exposed metrics, when they are inspected, then they contain no
  patient names, diagnoses, passwords or patient identifiers as labels.

## 4. Definition of Done

Every user story must satisfy the following conditions before it is
considered done. Individual tasks are completed when their specific
completion conditions are met and their pull request is merged with
passing required checks.

- Its acceptance criteria are satisfied.
- Changes are merged into main through a pull request, never pushed directly.
- Relevant unit tests are written and pass in CI.
- The end-to-end test for the affected workflow passes.
- Manual test cases, where defined, are executed and documented.
- Authorisation tests verify relevant allowed and denied access.
- The container image builds successfully and is published to
  GitHub Container Registry (GHCR).
- The documentation is updated if a requirement or design decision changes.
