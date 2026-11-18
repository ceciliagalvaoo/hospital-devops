# Story-point estimation

## 1. Estimation approach

Story points estimate the relative size of a complete user story, including implementation, testing, review and integration.

The estimate considers:

- Amount of work.
- Technical complexity.
- Uncertainty and unfamiliar technology.
- Dependencies and integration risk.
- Testing effort.

Story points do not represent hours. Epic totals are derived from their stories rather than estimated independently. Individual tasks are not given additional story points, avoiding double-counting.

## 2. Scale

| Points | Meaning |
| --- | --- |
| 1 | Trivial: a narrowly scoped, well-understood change with minimal logic and testing |
| 2 | Small: routine work that reuses existing patterns, with limited validation and a few tests |
| 3 | Standard: several implementation tasks, ordinary validation, permission checks and an end-to-end test |
| 5 | Substantial: multiple layers, meaningful business rules or integration work, with several boundary cases |
| 8 | Large or unfamiliar: significant security, infrastructure or integration uncertainty and extensive verification |
| 13 | Too large for sprint selection: split into smaller independently testable stories and re-estimate |

A smaller estimate still includes the relevant Definition of Done checks. It does not mean that tests or permissions can be omitted.

## 3. Reference story

**US-03 — Register a patient = 3 story points.**

This is the anchor because it includes a database entity, a migration, a validated endpoint, a form, permission checks and automated tests, while using familiar implementation patterns.

Other stories are estimated by comparing their overall effort, risk and testing needs with this reference.

## 4. Backlog estimates

| ID | User story | Epic | Points | Estimation rationale |
| --- | --- | --- | --- | --- |
| US-01 | Login and role-based access | E1 | 8 | Password handling, sessions, reusable permissions and security tests introduce significant risk |
| US-02 | Register a doctor | E3 | 5 | More complex than the anchor because it includes availability and staff-account association |
| US-03 | Register a patient | E2 | 3 | Reference story: standard validated registration with persistence, a form and tests |
| US-04 | Schedule an appointment | E4 | 8 | Combines entities, availability rules, transactional conflict protection and concurrent-booking tests |
| US-05 | View my appointments | E4 | 2 | A scoped list view using existing appointment data, with ownership tests |
| US-06 | Open a patient's record | E5 | 3 | A detail view with relationship-based authorisation and direct-access security tests |
| US-07 | Record a consultation | E5 | 5 | Adds clinical persistence, ownership checks and an atomic appointment-status transition |
| US-08 | Read previous medical records | E5 | 3 | A history query and view with ordering and sensitive-data access checks |
| US-09 | Search for a patient | E2 | 2 | Reuses the patient model and adds a limited query and result interface |
| US-10 | Edit patient contact details | E2 | 2 | A narrow update using existing validation and permission patterns |
| US-11 | Update an appointment | E4 | 5 | Reuses booking rules but must handle self-conflicts, availability changes and update boundaries |
| US-12 | Cancel an appointment | E4 | 3 | Includes status-transition rules, retained history and verification that the slot is released |
| US-13 | Update doctor details | E3 | 3 | Reuses registration patterns but includes availability validation |
| US-14 | Create staff accounts | E1 | 5 | Sensitive account creation, role assignment, unique logins and password handling |
| US-15 | Deactivate a staff account | E1 | 3 | Must reject both new login attempts and requests through existing sessions |
| US-16 | Deactivate a doctor | E3 | 3 | Soft deactivation, historical retention and integration with booking restrictions |
| US-17 | Deactivate a patient | E2 | 3 | Soft deactivation with appointment and medical-record retention checks |
| US-18 | Export authorised data | E5 | 5 | Sensitive-data filtering, CSV formatting, download tests and formula-input handling |
| US-19 | Filter the appointment calendar [Extra] | E4 | 2 | Reuses existing appointment queries with date and doctor filters |
| US-20 | Filter my medical records [Extra] | E5 | 2 | Reuses the authorised history query with date-boundary tests |
| US-21 | Filter staff accounts [Extra] | E1 | 2 | Adds simple filters to existing administrative account data |
| US-22 | Containerised application and database | E6 | 5 | Application scaffolding, containers, persistence, migrations and startup verification |
| US-23 | Continuous integration and merge checks | E6 | 8 | Integrates isolated databases, multiple test runners, container builds and required checks |
| US-24 | Automated container publication | E6 | 5 | Registry permissions, image tagging and verification of the published artifact |
| US-25 | Performance and recovery verification | E6 | 5 | Repeatable load scenarios, timing assertions, crash recovery and environment documentation |
| US-26 | Monitoring and metrics dashboard | E6 | 8 | Unfamiliar integration across application metrics, container metrics, Prometheus and Grafana |

## 5. Estimate summary

| Epic | Points |
| --- | --- |
| E1 — Authentication and access | 18 |
| E2 — Patient management | 10 |
| E3 — Doctor management | 11 |
| E4 — Appointment scheduling | 20 |
| E5 — Medical records and export | 18 |
| E6 — Platform and pipeline | 31 |
| **Total including optional stories** | **108** |
| **Required work excluding US-19 to US-21** | **102** |
| **Optional stories US-19 to US-21** | **6** |

These totals describe the backlog, not a guaranteed delivery commitment. The four-sprint forecast will be checked against available capacity and actual completed work.

## 6. Re-estimation and velocity

Before sprint selection, stories will be reviewed for unclear requirements, unresolved dependencies and excessive size.

- Any story estimated at 13 points will be split before entering a sprint.
- An 8-point story will be examined carefully and split if it cannot realistically finish within one sprint.
- New discoveries can change estimates before work is selected.
- Initial sprint capacity is a provisional forecast, because no historical velocity exists.
- Velocity counts only points from fully completed stories that satisfy the Definition of Done.
- Partially completed stories contribute zero points to completed velocity.
- Later sprint forecasts use measured completion and available capacity.
- Optional stories are deferred before required functionality or pipeline verification is removed.
