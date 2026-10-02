# Hospital Management — DevOps Project

## 1. Project overview
A simple hospital administration web application for managing
patients, doctors, appointments and medical records.
The project focuses on building an automated DevOps pipeline.

## 2. Requirement analysis

### 2.1 Functional requirements
- FR-01: Register, search, view and edit patients.
- FR-02: Deactivate patients while preserving past appointments.
- FR-03: Register, view, update and deactivate doctors.
- FR-04: Track doctors' specialisations and availability.
- FR-05: Create appointments with a patient, doctor, date, time and reason.
- FR-06: Support scheduled, completed and cancelled appointment statuses.
- FR-07: Prevent double-booking a doctor.
- FR-08: Allow doctors to record visit dates, diagnoses and notes.
- FR-09: Retain medical records and allow authorised staff to read them.
- FR-10: Require login before accessing protected functionality.
- FR-11: Restrict functionality according to the three user roles.
- FR-12: Allow doctors to export authorised data as CSV reports.

### 2.2 Non-functional requirements

- **NFR-01 — Performance:** At least 95% of page requests must complete within two seconds with 20 concurrent users against the seeded demo dataset.
- **NFR-02 — Recovery:** After an application process crashes, the container must restart automatically within 30 seconds using a declared restart policy.
- **NFR-03 — Password storage:** Passwords must be stored as bcrypt hashes with a cost factor of at least 10, never as plain text.
- **NFR-04 — Access control:** Every protected route must enforce authentication and role permissions, returning HTTP 401 for unauthenticated requests and HTTP 403 for forbidden actions.
- **NFR-05 — Deployability:** Every source change merged into main that passes the pipeline must automatically build and publish a container image to GHCR.
- **NFR-06 — Testability:** Automated unit and end-to-end tests must run in CI on every pull request, and failed required checks must prevent merging.
- **NFR-07 — Observability:** Request counts, error rates, response times and container CPU and memory usage must be visible on a dashboard with a refresh interval of no more than 30 seconds.
- **NFR-08 — Maintainability:** The README must document the branching strategy and image versioning scheme; published images must include a commit SHA tag for traceability.

## 3. Roles and access control

### 3.1 User roles

- **Receptionist:** Manages patient administrative records and the appointment calendar. Registers, searches, edits and deactivates patients, and schedules, updates and cancels appointments, without accessing clinical notes.

- **Doctor:** Views their own appointments and the medical history of their patients. Records visit dates, diagnoses and notes, and exports authorised data to CSV.

- **Administrator:** Manages doctor records, system user accounts and role assignments. Also manages patient administrative records and appointments, without accessing clinical information.

Patients are data entities, not system users. A patient login role was considered and excluded because the scenario does not provide patient self-service functionality.

### 3.2 RBAC matrix

RBAC stands for Role-Based Access Control.

| Capability | Receptionist | Doctor | Administrator |
|---|---|---|---|
| Register, search and edit a patient | Yes | No | Yes |
| Deactivate a patient record | Yes | No | Yes |
| Register, update or deactivate a doctor | No | No | Yes |
| Schedule an appointment | Yes | No | Yes |
| View appointments | All | Own only | All |
| Update appointment details or cancel an appointment | Yes | No | Yes |
| Record diagnosis and visit notes | No | Own appointments only | No |
| Read a patient's medical history | No | Own patients only | No |
| Export authorised data to CSV | No | Own patients' authorised data only | No |
| Manage user accounts and roles | No | No | Yes |

### 3.3 Decisions for ambiguous permissions

- **Doctors cannot reschedule or cancel appointments:** Calendar administration is assigned to receptionists and administrators; doctors remain responsible for clinical documentation.
- **Administrators cannot read medical histories:** Their role is administrative, so clinical information is restricted to authorised doctors.
- **Administrators cannot export data to CSV:** The scenario assigns export functionality to doctors, so no additional export permission is granted.

### 3.4 Access enforcement

Permissions must be enforced on the server for every protected route.
Unauthenticated requests are rejected with HTTP 401, and authenticated
users without the required permission receive HTTP 403.

Doctor access must also verify the relationship between the doctor
and the requested appointment or patient. Hiding interface elements
alone is not sufficient.

Automated authorisation tests must verify every denied permission
and confirm that doctors cannot access another doctor's appointments
or patients outside their authorised scope.

## 4. Product backlog

### 4.1 Ordered user stories

The following list is ordered by implementation priority, considering
dependencies, risk and business value. Story identifiers remain stable
if the backlog is reordered.

1. **US-01 — Login and role-based access**
   As a receptionist, doctor or administrator, I want to log in and
   access only the functionality permitted for my role, so that
   hospital information is protected against unauthorised access.

2. **US-02 — Register a doctor**
   As an administrator, I want to register a doctor with their
   specialisation and availability, so that receptionists can
   assign appointments to an appropriate available doctor.

3. **US-03 — Register a patient**
   As a receptionist, I want to register a patient with their name,
   date of birth and contact details, so that the patient can
   be booked for an appointment.

4. **US-04 — Schedule an appointment**
   As a receptionist, I want to schedule an appointment with a
   patient, doctor, date, time and reason without double-booking,
   so that patients receive a confirmed consultation slot.

5. **US-05 — View my appointments**
   As a doctor, I want to view my scheduled appointments,
   so that I can prepare for upcoming consultations.

6. **US-06 — Open a patient's record**
   As a doctor, I want to open the record of a patient assigned
   to my appointment, so that I can identify the patient
   correctly before providing care.

7. **US-07 — Record a consultation**
   As a doctor, I want to record the visit date, diagnosis and
   notes and mark the appointment as completed, so that future
   care can rely on documented consultation outcomes.

8. **US-08 — Read previous medical records**
   As a doctor, I want to read previous medical records of my
   authorised patients, so that I can make informed clinical decisions.

9. **US-09 — Search for a patient**
   As a receptionist, I want to search for an existing patient,
   so that I can locate the correct record without creating duplicates.

10. **US-10 — Edit patient contact details**
    As a receptionist, I want to update a patient's contact details,
    so that the hospital can reach them using current information.

11. **US-11 — Update an appointment**
    As a receptionist, I want to change appointment details while
    respecting doctor availability and preventing double-booking,
    so that changes in patient needs can be accommodated.

12. **US-12 — Cancel an appointment**
    As a receptionist, I want to cancel an appointment while retaining
    its record, so that the slot becomes available and the hospital
    preserves the scheduling history.

13. **US-13 — Update doctor details**
    As an administrator, I want to update a doctor's details and
    availability, so that appointment scheduling uses accurate information.

14. **US-14 — Create staff accounts**
    As an administrator, I want to create a staff account and assign
    one of the three supported roles, so that new staff members
    receive appropriate system access.

15. **US-15 — Deactivate a staff account**
    As an administrator, I want to deactivate a staff account,
    so that former staff members can no longer access hospital information.

16. **US-16 — Deactivate a doctor**
    As an administrator, I want to deactivate an unavailable doctor
    while preserving past appointments, so that new appointments
    cannot be assigned to that doctor and historical information remains.

17. **US-17 — Deactivate a patient**
    As a receptionist, I want to deactivate a patient record while
    preserving past appointments and medical records, so that inactive
    patients are excluded from new bookings without losing their history.

18. **US-18 — Export authorised data**
    As a doctor, I want to export my authorised data as a CSV report,
    so that I can analyse consultation information outside the application.

19. **US-19 — Filter the appointment calendar [Extra: Receptionist]**
    As a receptionist, I want to filter appointments by date and doctor,
    so that I can answer scheduling questions more quickly.

20. **US-20 — Filter my medical records [Extra: Doctor]**
    As a doctor, I want to filter my authorised patients' medical
    records by visit date, so that I can find relevant consultations
    efficiently during follow-up care.

21. **US-21 — Filter staff accounts [Extra: Administrator]**
    As an administrator, I want to filter staff accounts by role
    and active status, so that I can review access assignments efficiently.

### 4.2 Prioritisation rationale

Login and role-based access come first because every protected workflow
depends on identifying staff and enforcing permissions.
Doctor registration comes second and patient registration third because
both are prerequisites for scheduling, with doctor availability
establishing the scheduling constraints before bookings are introduced.

### 4.3 Acceptance criteria

#### US-01 — Login and role-based access

- Given an active staff account with valid credentials, when the staff
  member logs in, then the system grants access according to their role.
- Given invalid credentials or an inactive account, when login is
  attempted, then access is refused.
- Given an unauthenticated request to a protected route, when the
  request is processed, then the system returns HTTP 401.
- Given an authenticated staff member without the required permission,
  when they request a restricted action, then the system returns HTTP 403.

#### US-03 — Register a patient

- Given an authenticated receptionist and valid patient information,
  when registration is submitted, then the patient is saved and
  can be found through patient search.
- Given a missing required name or date of birth, when registration
  is submitted, then the system rejects it and identifies the missing fields.
- Given an authenticated doctor, when they attempt to register a
  patient, then the system refuses the action.

#### US-04 — Schedule an appointment

- Given an active patient, an active doctor and an available slot,
  when a receptionist submits all required appointment details,
  then the system creates an appointment with status "scheduled".
- Given a doctor already has a scheduled appointment at a particular
  date and time, when another booking is attempted for that same
  doctor and slot, then the system rejects it and explains the conflict.
- Given an inactive patient, an inactive doctor or a slot outside
  the doctor's availability, when booking is attempted, then
  the system rejects the appointment.

#### US-07 — Record a consultation

- Given a doctor assigned to a scheduled appointment, when they
  submit a visit date, diagnosis and notes and complete the consultation,
  then the system saves the medical record and marks the appointment
  as "completed".
- Given a receptionist, administrator or an unassigned doctor,
  when they attempt to record clinical information for that appointment,
  then the system refuses the action.
- Given a saved medical record, when an authorised doctor opens
  the patient's history, then the consultation information is displayed.

### 4.4 Definition of Done

Every implementation task must satisfy the following conditions
before it is considered done:

- Its acceptance criteria are satisfied.
- Changes are merged into main through a pull request, never pushed directly.
- Relevant unit tests are written and pass in CI.
- The end-to-end test for the affected workflow passes.
- Authorisation tests verify relevant allowed and denied access.
- The container image builds successfully and is published to
  GitHub Container Registry (GHCR).
- The README is updated if a requirement or design decision changes.

## 5. Process and ceremonies

### 5.1 Sprint duration

The initial plan consists of four two-week sprints, covering eight weeks.
Two weeks provide enough time to deliver a working increment alongside
other coursework while allowing frequent feedback and adjustments.

This is an individual project, so I will perform the Product Owner,
developer and Scrum Master responsibilities.

### 5.2 Sprint outline

| Sprint | Goal | Planned deliverables |
|---|---|---|
| 1 | Establish a working application and pipeline | Login and role-based access (US-01), basic doctor registration (US-02), database persistence, repository conventions, branching strategy, containerisation and CI build and tests. |
| 2 | Deliver patient and doctor administration | Patient registration, search and editing (US-03, US-09, US-10), doctor updates and deactivation (US-13, US-16), patient deactivation (US-17), staff account creation and deactivation (US-14, US-15). |
| 3 | Deliver the consultation workflow | Scheduling without double-booking (US-04), doctor appointment and patient views (US-05, US-06), clinical notes and history (US-07, US-08), appointment updates and cancellation (US-11, US-12), CSV export (US-18). |
| 4 | Verify quality and prepare the defence | Expand end-to-end and authorisation tests, verify performance and failure recovery, add monitoring and a metrics dashboard, complete documentation and implement extra stories (US-19–US-21) if capacity permits. |

Container image publication to GHCR and an end-to-end smoke test
will be established in Sprint 1 to support the Definition of Done.
Each later sprint will extend the tests alongside its functionality.

The outline is a forecast. At each planning session, stories will be
selected according to capacity and dependencies. Any story too large
for one sprint will be split, and unfinished work will be re-estimated
and reprioritised.

### 5.3 Ceremonies

| Ceremony | When | Activity | Output |
|---|---|---|---|
| Sprint Planning | First day of each sprint, 30–60 minutes | Review the ordered backlog, check dependencies and acceptance criteria, and select realistic work. | Sprint goal and sprint backlog. |
| Sprint Review | Last day of each sprint, approximately 30 minutes | Run the working application, check completed stories against their acceptance criteria and demonstrate it to a classmate or instructor for feedback. | Recorded feedback and an updated product backlog. |
| Sprint Retrospective | Immediately after the review, approximately 20 minutes | Review progress, blockers and working practices, then choose one improvement for the next sprint. | A written retrospective and one concrete improvement action. |

As this is an individual project, I will keep a short dated work log
instead of holding a Daily Scrum. Each entry will record completed work,
the next action and any blockers.

Planning, review and retrospective notes will be stored in the repository.

### 5.4 Backlog refinement

Refinement will be continuous, with approximately 10% of available
sprint working time reserved for clarifying and preparing upcoming work.

The following events will trigger refinement:

- **New or changed requirement:** Add or update stories and acceptance criteria.
- **Story too large for one sprint:** Split it into smaller, testable stories.
- **Missing or unclear acceptance criteria:** Clarify the expected behaviour before selecting the story.
- **Unfinished sprint work:** Re-estimate the remaining effort and reconsider its priority.
- **Technical discovery:** Update tasks and ordering when a constraint or dependency is discovered.
- **Sprint Review feedback:** Adjust the backlog based on the demonstration and feedback.

Changes affecting requirements or permissions will also be reflected
in the requirement analysis and RBAC matrix.
