# Sprint planning

## 1. Process and ceremonies

### 1.1 Sprint duration

The initial plan consists of four two-week sprints, covering eight weeks.
Two weeks provide enough time to deliver a working increment alongside
other coursework while allowing frequent feedback and adjustments.

This is an individual project, so I will perform the Product Owner,
developer and Scrum Master responsibilities.

### 1.2 Sprint outline

| Sprint | Goal | Planned deliverables |
|---|---|---|
| 1 | Establish a containerised application with secure login, automated checks and traceable image publication | Containerised application and database (US-22), login and role-based access (US-01), CI and required merge checks (US-23), GHCR image publication (US-24), repository conventions and branching strategy. |
| 2 | Deliver patient and doctor registration and administrative account management | Doctor registration and updates (US-02, US-13), patient registration, search and editing (US-03, US-09, US-10), staff account creation and deactivation (US-14, US-15). |
| 3 | Deliver the appointment and consultation workflow with authorised access to medical history | Scheduling without double-booking (US-04), doctor appointment and patient views (US-05, US-06), clinical notes and history (US-07, US-08), appointment cancellation (US-12). |
| 4 | Complete administrative workflows and export, and verify performance, recovery and monitoring | Appointment updates (US-11), doctor and patient deactivation (US-16, US-17), CSV export (US-18), performance and recovery verification (US-25), monitoring and a metrics dashboard (US-26); extra stories (US-19–US-21) if capacity permits. |

Container image publication to GHCR and an end-to-end smoke test
will be established in Sprint 1 to support the Definition of Done.
Each later sprint will extend the tests alongside its functionality.
The detailed sprint backlogs and point totals are in §2.

The outline is a forecast. At each planning session, stories will be
selected according to capacity and dependencies. Any story too large
for one sprint will be split, and unfinished work will be re-estimated
and reprioritised.

### 1.3 Ceremonies

| Ceremony | When | Activity | Output |
|---|---|---|---|
| Sprint Planning | First day of each sprint, 30–60 minutes | Review the ordered backlog, check dependencies and acceptance criteria, and select realistic work. | Sprint goal and sprint backlog. |
| Sprint Review | Last day of each sprint, approximately 30 minutes | Run the working application, check completed stories against their acceptance criteria and demonstrate it to a classmate or instructor for feedback. | Recorded feedback and an updated product backlog. |
| Sprint Retrospective | Immediately after the review, approximately 20 minutes | Review progress, blockers and working practices, then choose one improvement for the next sprint. | A written retrospective and one concrete improvement action. |

As this is an individual project, I will keep a short dated work log
instead of holding a Daily Scrum. Each entry will record completed work,
the next action and any blockers.

Planning, review and retrospective notes and the work log are stored in the repository, one file per sprint in [docs/sprints/](sprints), starting with [docs/sprints/sprint-1.md](sprints/sprint-1.md).

### 1.4 Backlog refinement

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

## 2. Projected sprint backlogs

### 2.1 Sprint duration and planning assumptions

The project is planned as four two-week sprints, covering eight weeks, as defined in §1.1.

The following backlogs are an initial forecast rather than a delivery commitment. No historical velocity is available yet. The forecast allocates all 102 points of required work, while the six points of optional stories remain outside the baseline.

Available capacity is estimated at about 6 hours per week, or 12 hours per two-week sprint, alongside other coursework. Story points are not converted into hours. The 26-point Sprint 1 forecast is therefore an opening bid rather than a measured capacity: Sprint 1 is expected to reveal the real velocity, and it is deliberately loaded with the foundation work that every later story depends on.

If Sprint 1 completes fewer points than forecast, the measured velocity will replace the forecast from Sprint 2 onwards. The project remains limited to four sprints, so work that does not fit the measured velocity is deferred in the following order:

1. Optional stories US-19, US-20 and US-21.
2. US-18 — Export authorised data.
3. US-11 — Update an appointment.
4. US-13 — Update doctor details.
5. US-14 and US-15 — Staff account creation and deactivation; the administrator then continues to use seeded staff accounts.

The platform and pipeline stories (US-22 to US-26) and the appointment and consultation workflow shown in the activity diagram (US-01 to US-07 and US-09) are never deferred. Deferred stories return to the Product Backlog with their estimates. Deferring a required story does not remove its associated requirement. Any reduction in the required delivery scope must be discussed with the instructor and documented in the sprint review.

Sprint Planning will confirm the selected work according to available capacity, dependencies and the results of previous sprints. If measured capacity is insufficient, the remaining backlog will be revised using the deferral order above.

Testing, review and integration are included in each story's estimate. They are performed throughout development rather than postponed to the final sprint.

### 2.2 Sprint overview

| Sprint | Goal | Planned stories | Points |
| --- | --- | --- | --- |
| 1 | Establish a containerised application with secure login, automated checks and traceable image publication | US-22, US-01, US-23, US-24 | 26 |
| 2 | Deliver patient and doctor registration and administrative account management | US-02, US-03, US-09, US-10, US-13, US-14, US-15 | 23 |
| 3 | Deliver the appointment and consultation workflow with authorised access to medical history | US-04, US-05, US-06, US-07, US-08, US-12 | 24 |
| 4 | Complete administrative workflows and export, and verify performance, recovery and monitoring | US-11, US-16, US-17, US-18, US-25, US-26 | 29 |
| **Total** | | **Required backlog** | **102** |

### 2.3 Sprint 1 — Application and delivery foundation

**Goal:** Establish a containerised application with secure login, automated checks and traceable image publication.

| Story | Deliverable | Points |
| --- | --- | --- |
| US-22 | FastAPI application, PostgreSQL, migrations and reproducible container startup | 5 |
| US-01 | Login, logout, seeded staff accounts and role enforcement | 8 |
| US-23 | CI for unit, integration and end-to-end tests, container builds and required merge checks | 8 |
| US-24 | Automatic GHCR publication with commit-SHA tags and published-image verification | 5 |
| **Total** | | **26** |

Implementation order:
1. Create the application structure and container environment.
2. Implement accounts, authentication and role checks.
3. Introduce tests and CI alongside implementation.
4. Add the login end-to-end test to CI.
5. Enable required checks and image publication after successful checks.

US-01 and the pipeline are developed together. Login implementation does not wait for a completed pipeline, but neither story is counted as done until its required checks pass.

**Review evidence:** Demonstrate container startup, login for each role, denied access, a successful pipeline run, a failed-check example and a published image linked to its commit.

### 2.4 Sprint 2 — Registration and administration

**Goal:** Deliver patient and doctor registration and administrative account management.

| Story | Deliverable | Points |
| --- | --- | --- |
| US-02 | Register doctors with specialisation and availability | 5 |
| US-03 | Register patients | 3 |
| US-09 | Search for patients | 2 |
| US-10 | Edit patient contact details | 2 |
| US-13 | Update doctor details and availability | 3 |
| US-14 | Create staff accounts and assign roles | 5 |
| US-15 | Deactivate staff accounts and reject subsequent access | 3 |
| **Total** | | **23** |

Implementation order:
1. Register doctor profiles and patients using the existing authentication foundation.
2. Add patient search and contact editing.
3. Add doctor updates.
4. Implement account creation before account deactivation.

US-03 and US-09 are completed in the same sprint so that the patient-registration acceptance criterion involving search can be verified.

Doctor registration initially uses seeded doctor accounts; it does not depend on the account-management interface being implemented first.

**Review evidence:** Demonstrate registration, search, updates, account creation and deactivation, including denied actions for unauthorised roles.

### 2.5 Sprint 3 — Appointments and clinical workflow

**Goal:** Deliver the appointment and consultation workflow with authorised access to medical history.

| Story | Deliverable | Points |
| --- | --- | --- |
| US-04 | Schedule appointments with availability and double-booking protection | 8 |
| US-05 | Show each doctor their own appointments | 2 |
| US-06 | Allow doctors to open assigned patients' records | 3 |
| US-07 | Record consultations and complete appointments | 5 |
| US-08 | Read authorised patients' medical histories | 3 |
| US-12 | Cancel appointments while preserving history and releasing slots | 3 |
| **Total** | | **24** |

Implementation order:
1. Implement appointment creation and booking rules.
2. Add the doctor's appointment list and authorised patient view.
3. Add clinical documentation and the completed status.
4. Add medical-history retrieval.
5. Add cancellation and slot-release verification.

US-04 requires patient and doctor registration from Sprint 2. Clinical stories follow their dependency chain: US-05 → US-06 → US-07 → US-08.

**Review evidence:** Demonstrate booking, refusal of conflicting bookings, doctor-specific access, consultation completion, medical history and cancellation. Include negative authorisation tests and concurrent-booking verification.

### 2.6 Sprint 4 — Completion and operational verification

**Goal:** Complete administrative workflows and export, and verify performance, recovery and monitoring.

| Story | Deliverable | Points |
| --- | --- | --- |
| US-11 | Update appointments while preserving booking rules | 5 |
| US-16 | Deactivate doctors without deleting historical appointments | 3 |
| US-17 | Deactivate patients without deleting historical appointments or medical records | 3 |
| US-18 | Export authorised clinical data to CSV | 5 |
| US-25 | Verify response-time and container-recovery requirements | 5 |
| US-26 | Display application and container metrics on a dashboard | 8 |
| **Total** | | **29** |

All required appointment and medical-record dependencies are available from Sprint 3. History-preservation tests for US-16 and US-17 are therefore completed in this sprint.

Monitoring can begin earlier if capacity permits because it depends on the container foundation rather than the clinical workflow.

This sprint has the largest forecast. Its scope will be reviewed against measured velocity before selection. Operational verification remains part of the required backlog.

**Review evidence:** Demonstrate rescheduling, deactivation with retained history, scoped CSV export, performance results, automatic recovery and a refreshing metrics dashboard.

The final review also checks documentation, the activity diagram and traceability between requirements, issues, branches, pull requests, tests and published images.

### 2.7 Optional backlog

The following stories are excluded from the 102-point baseline:

| Story | Optional deliverable | Points |
| --- | --- | --- |
| US-19 | Filter the appointment calendar by date and doctor | 2 |
| US-20 | Filter authorised medical records by visit date | 2 |
| US-21 | Filter staff accounts by role and active status | 2 |
| **Total** | | **6** |

They may be selected when required work is complete and capacity remains. They will not replace required tests, monitoring or delivery work.

### 2.8 Tracking and replanning

- Sprint items will be tracked in the repository-linked GitHub Project.
- The Sprint field will use two-week iterations.
- Status values are Backlog, Ready, In Progress, In Review and Done (see [github-project.md](github-project.md) §4).
- Only stories satisfying the Definition of Done contribute to velocity.
- Unfinished work returns to planning for dependency, estimate and priority review.
- Sprint reviews and retrospectives are recorded in the repository, in [docs/sprints/](sprints).
- Changes to this forecast will also be reflected in the sprint outline in §1.2.
