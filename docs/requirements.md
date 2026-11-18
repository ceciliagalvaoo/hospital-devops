# Requirements

## 1. Requirement analysis

### 1.1 Functional requirements
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

### 1.2 Non-functional requirements

- **NFR-01 — Performance:** At least 95% of page requests must complete within two seconds with 20 concurrent users against the seeded demo dataset.
- **NFR-02 — Recovery:** After an application process crashes, the container must restart automatically within 30 seconds using a declared restart policy.
- **NFR-03 — Password storage:** Passwords must be stored as bcrypt hashes with a cost factor of at least 10, never as plain text.
- **NFR-04 — Access control:** Every protected route must enforce authentication and role permissions, returning HTTP 401 for unauthenticated requests and HTTP 403 for forbidden actions.
- **NFR-05 — Deployability:** Every source change merged into main that passes the pipeline must automatically build and publish a container image to GHCR.
- **NFR-06 — Testability:** Automated unit and end-to-end tests must run in CI on every pull request, and failed required checks must prevent merging.
- **NFR-07 — Observability:** Request counts, error rates, response times and container CPU and memory usage must be visible on a dashboard with a refresh interval of no more than 30 seconds.
- **NFR-08 — Maintainability:** The project documentation must describe the branching strategy and image versioning scheme; published images must include a commit SHA tag for traceability.

## 2. Roles and access control

### 2.1 User roles

- **Receptionist:** Manages patient administrative records and the appointment calendar. Registers, searches, edits and deactivates patients, and schedules, updates and cancels appointments, without accessing clinical notes.

- **Doctor:** Views their own appointments and the medical history of their patients. Records visit dates, diagnoses and notes, and exports authorised data to CSV.

- **Administrator:** Manages doctor records, system user accounts and role assignments. Also manages patient administrative records and appointments, without accessing clinical information.

Patients are data entities, not system users. A patient login role was considered and excluded because the scenario does not provide patient self-service functionality.

### 2.2 RBAC matrix

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

### 2.3 Decisions for ambiguous permissions

- **Doctors cannot reschedule or cancel appointments:** Calendar administration is assigned to receptionists and administrators; doctors remain responsible for clinical documentation.
- **Administrators cannot read medical histories:** Their role is administrative, so clinical information is restricted to authorised doctors.
- **Administrators cannot export data to CSV:** The scenario assigns export functionality to doctors, so no additional export permission is granted.

### 2.4 Access enforcement

Permissions must be enforced on the server for every protected route.
Unauthenticated requests are rejected with HTTP 401, and authenticated
users without the required permission receive HTTP 403.

Doctor access must also verify the relationship between the doctor
and the requested appointment or patient. Hiding interface elements
alone is not sufficient.

Automated authorisation tests must verify every denied permission
and confirm that doctors cannot access another doctor's appointments
or patients outside their authorised scope.
