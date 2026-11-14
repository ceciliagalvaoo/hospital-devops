# Sprint 1 — Application and delivery foundation

| | |
| --- | --- |
| Dates | 2026-11-01 to 2026-11-14 (two weeks) |
| Goal | Establish a containerised application with secure login, automated checks and traceable image publication |
| Planned stories | US-22, US-01, US-23, US-24 (26 points) |
| Planning | Held on 2026-11-04, recorded on 2026-11-07 (#185) |
| Review and retrospective | 2026-11-14 (#186) |
| Release | `v0.2.0` (#186) |

This file is the record of the sprint ceremonies required by README §5.3: the planning, the work log that replaces the Daily Scrum, and the review and retrospective. The planning section reflects the decisions as taken; later changes are recorded in the work log.

## 1. Sprint Planning

### 1.1 Goal and selected stories

The goal and the stories come from the projected sprint backlog in README §8.3.

| Story | Issue | Deliverable | Points | Priority |
| --- | --- | --- | --- | --- |
| US-22 | #131 | FastAPI application, PostgreSQL, migrations and reproducible container startup | 5 | P0 |
| US-01 | #3 | Login, logout, seeded staff accounts and role enforcement | 8 | P0 |
| US-23 | #137 | CI for unit, integration and end-to-end tests, container builds and required merge checks | 8 | P0 |
| US-24 | #145 | Automatic GHCR publication with commit-SHA tags and published-image verification | 5 | P0 |
| **Total** | | | **26** | |

### 1.2 Capacity

Capacity is estimated at about 6 hours per week, or 12 hours per sprint, alongside other coursework (README §8.1). No historical velocity exists, so the 26-point forecast is an opening bid: this sprint measures the real velocity, which replaces the forecast from Sprint 2 onwards. If the work does not fit, the deferral order in README §8.1 applies.

### 1.3 State at the planning

| Story | Done | Remaining tasks |
| --- | --- | --- |
| US-22 | T-22.1 (#132), merged on 2026-10-23 | T-22.2 to T-22.5 (#133–#136) |
| US-01 | — | T-01.1 to T-01.9 (#5–#13) |
| US-23 | — | T-23.1 to T-23.7 (#138–#144) |
| US-24 | — | T-24.1 to T-24.4 (#146–#149) |

T-22.1 was completed before the sprint started, together with the Lab 4 and Lab 5 coursework (#162, #167). These items keep Sprint 1 in their Sprint field because they belong to its foundation.

### 1.4 Task sequence

Dependencies were checked against README §6 and the order was fixed so that every task starts unblocked. Tasks are worked strictly one at a time, each through the full cycle: issue in progress, branch from the issue, commits, tests, pull request, self-review, merge, issue done, branch deleted. The split into two weeks only organises the work.

**Week 1**

1. US-22: #133 Dockerfile → #134 Docker Compose → #135 migrations and startup → #136 container smoke test.
2. US-23: #138 pytest fixtures and test database → #139 CI workflow → #142 CI smoke test and failing check → #144 container build in CI.
3. US-01: #5 staff account model → #6 seed command → #7 login, logout and sessions.

**Week 2**

1. US-01: #8 401/403 checks → #13 CSRF → #9 login interface → #10 automated tests → #11 Playwright tests → #12 manual tests.
2. US-23: #140 Playwright in CI → #141 required checks → #143 manual check that failed checks block merging.
3. US-24: #146 main-branch publication → #147 tags and versioning → #148 published-image smoke check → #149 manual publication checks.
4. Closing: DOC-02 (#193) architecture → review, retrospective and release (#186).

### 1.5 Decisions

- **Stories close together.** The Definition of Done (README §4.4) requires passing CI checks and an image published to GHCR. US-22, US-01 and US-23 therefore stay open until US-24 publishes the image, and the four stories are closed together at the end of the sprint. Velocity counts only fully done stories (README §7.6).
- **No production deployment.** Delivery is the publication of the image to GHCR; a running deployment is out of scope (README §9.3).
- **Lab 6.** Task 8 of Lab 6 (containerising the project) is done in this repository as LAB6-08 (#181); the report on Tasks 0–7 is added as LAB6-REPORT (#183).

The following decisions were taken during the sprint, on 2026-11-07:

- **Sprint length.** The Sprint 1 iteration in the GitHub Project lasted 30 days (2026-10-16 to 2026-11-14). It was shortened to the standard two weeks (2026-11-01 to 2026-11-14) defined in README §5.1, keeping the end date, so Sprints 2 to 4 keep their dates and the project still ends on 2026-12-26.
- **Ceremony tasks.** Each sprint has a planning task (SPRINTn-01) that closes on the planning day, and a review and retrospective task (SPRINTn-02) that closes the sprint: #185/#186, #187/#188, #189/#190 and #191/#192. After this record, the pull request of each task adds its own work-log entry.
- **One release per sprint.** Each review task publishes a release on `main`: `v0.2.0` for Sprint 1, then `v0.3.0`, `v0.4.0` and `v1.0.0` (docs/branching-strategy.md §4).
- **Architecture document.** DOC-02 (#193) documents the implemented architecture in `docs/architecture.md` before the review, and each later review keeps it up to date.

## 2. Work log

Each entry records the completed work, the next action and any blockers. Entries up to 2026-11-07 were reconstructed from the issues, pull requests and commits.

### 2026-11-04

- **Done:**
  - Sprint Planning (§1).
  - US-22: #133 (PR #170), #134 (PR #171), #135 (PR #172) and #136 (PR #173). All US-22 tasks are done; the story waits for GHCR publication.
  - US-23: #138 (PR #174), #139 (PR #175), #142 (PR #176) and #144 (PR #177). CI runs the `Lint`, `Tests` and `Container` jobs on every pull request.
  - US-01: #5 (PR #178), #6 (PR #179) and #7 (PR #180).
  - Lab 6: Task 8 as #181 (PR #182, multi-stage Dockerfile and `docs/docker-build.md`) and the report on Tasks 0–7 as #183 (PR #184).
  - Created the standalone task DOC-01 (#169) for Sprint 2.
- **Next:** #8, reusable 401/403 checks.
- **Blockers:** none. #7 did not close automatically from `Closes #7` and was closed by hand.

### 2026-11-07

- **Done:**
  - Shortened the Sprint 1 iteration to 2026-11-01 to 2026-11-14.
  - Created the ceremony tasks #185 to #192, DOC-02 (#193) and the release criteria.
  - Reviewed `docs/` against the plan: refinement notes on #141 and #147, and a review of the branching strategy added to the retrospective (#186).
  - US-01: #8 (PR #194).
  - This planning record (#185).
  - US-01: #13, CSRF protection for every state-changing request.
  - US-01: #9, login pages and role-based navigation, with placeholder area pages for the Sprint 1 review.
  - US-01: #10, the remaining authentication test cases and the US-01 test map (`docs/testing/us-01-automated-tests.md`).
  - US-01: #11, Playwright end-to-end tests for login, navigation and logout per role (`pytest -m e2e`).
  - Preparing #12, a browser pre-check found defect #202: the administrator's home page scrolled horizontally on a 320 px screen. Fixed with wrapping of long words and covered by end-to-end tests at 320 px.
  - US-01: #12, manual checks of login messages, keyboard navigation and small screens in Chrome 156 on Windows 11: 19 of 20 pass. The expired-form page is titled "Access denied" (A8), recorded as defect #204.
  - US-01: #204, error pages are titled by their reason ("Form expired", "Request refused", "Access denied", "Page not found"); covered by tests that reproduced the defect.
  - US-01: all tasks done; the story waits for the end-to-end tests in CI and GHCR publication.
  - US-23: #140, a CI job `E2E` runs the browser tests and keeps screenshots, videos and traces of failures.
  - US-23: #141, the ruleset of `main` requires the checks `Lint`, `Tests`, `E2E` and `Container` with an up-to-date branch, and allows only merge commits.
  - US-23: #143, a throwaway pull request (#209, closed without merging) showed that running or failed required checks and an outdated branch block the merge, also for the administrator: 6 of 6 checks pass. All US-23 tasks are done.
  - US-24: #146, a CI job `Publish` pushes the image to GHCR after the required checks pass on `main`.
  - US-24: #146 verified on `main`: the first image was published to GHCR (public package, anonymous pull works).
  - US-24: #147, published images carry `sha-<commit>` tags and version and revision labels; release tags `vX.Y.Z` also publish `X.Y.Z`, `X.Y` and `latest` (decision of 2026-11-07).
  - US-24: #147 verified on `main`: `main` and `sha-6b0482d` published with the version and revision labels.
  - US-24: #148, a CI job `Verify image` pulls the published image anonymously and checks health, login page, user and labels; run locally against `sha-6b0482d`: 7 of 7 passed.
  - US-24: #148 verified on `main`: `Verify image` pulled `sha-4fcbce3` anonymously and passed 7 of 7 checks.
  - US-24: #149, manual checks: pull requests and manual runs do not publish, and the image of `4fcbce3` matches its commit (digest, revision label, 29 application files, 8 dependencies); 6 of 6 pass. All US-24 tasks are done.
  - The four Sprint 1 stories meet their acceptance criteria and Definition of Done and stay *In Progress* until they are accepted in the Sprint Review (they were first moved to *In Review*, which README §10.4 reserves for open pull requests, and moved back).
  - #193, `docs/architecture.md`: overview, modules, data model, request flow, delivery, tests, configuration and design decisions, with four Mermaid diagrams.
- **Next:** #186, Sprint Review, Retrospective and release `v0.2.0` on 2026-11-14.
- **Blockers:** none.

### 2026-11-10 and 2026-11-11

- **Done:**
  - Lab 7 planned: Tasks 0–5 in the separate repository `testing-demo`, report as LAB7-REPORT (#218); Task 6 in this project as #216, #217 and #219, moved to Sprint 2 on 2026-11-11.
  - #218, the Lab 7 report (`docs/testing-lab.md`) with its evidence in `docs/lab7-evidence/`.
- **Next:** #186, Sprint Review, Retrospective and release `v0.2.0` on 2026-11-14.
- **Blockers:** none. A network error while creating the Lab 7 issues produced a duplicate, #220, closed as not planned.

### 2026-11-12

- **Done:** Sprint Review demonstration to a classmate (§4).
- **Next:** #186, review record, retrospective and release.
- **Blockers:** none.

### 2026-11-14

- **Done:**
  - Sprint Review (§4): the four stories accepted and closed, velocity 26 points; defect #222 registered for Sprint 2.
  - Sprint Retrospective (§5), with the branching strategy kept and one improvement action.
  - README §10.4 and §10.5: WIP limits count tasks and defects only; the Kanban view shows tasks and defects.
  - Release `v0.2.0` prepared (#186).
- **Next:** Sprint 2 planning (#187) on 2026-11-15.
- **Blockers:** none.

## 3. Increment

The increment of Sprint 1 is the application foundation: a containerised FastAPI application with PostgreSQL and migrations, secure login with role-based access, a CI pipeline with four required checks, and automatic, verified publication of the image to GHCR. The implemented architecture is documented in [docs/architecture.md](../architecture.md).

| Story | What it added | Pull requests | Documentation |
| --- | --- | --- | --- |
| US-22 (#131), 5 points | FastAPI application with `/health`, non-root multi-stage image, Docker Compose with PostgreSQL and persistence, migrations as a gating one-off service, container smoke tests | #165 (before the sprint), #170, #171, #172, #173, #182 (Lab 6) | README §11, [docker-build.md](../docker-build.md) |
| US-01 (#3), 8 points | Staff accounts with bcrypt, development seed, server-side sessions, reusable 401/403 checks, CSRF protection, login pages and role-based navigation, automated and end-to-end tests, manual checks; defects #202 and #204 found by the tests and fixed | #178, #179, #180, #194, #198, #199, #200, #201, #203, #205, #206 | README §11, [testing/us-01-automated-tests.md](../testing/us-01-automated-tests.md), [testing/us-01-manual-checks.md](../testing/us-01-manual-checks.md) |
| US-23 (#137), 8 points | Pytest fixtures with an isolated test database, CI jobs `Lint`, `Tests`, `E2E` (Playwright, with failure artifacts) and `Container`, a deliberate-failure check, the four jobs as required checks of `main` with merge commits only, and the manual proof that failed checks block merging | #174, #175, #176, #177, #207, #208, #210 | README §11, [branching-strategy.md](../branching-strategy.md) §3 and §7, [git-workflow.md](../git-workflow.md) §5, [testing/us-23-manual-checks.md](../testing/us-23-manual-checks.md) |
| US-24 (#145), 5 points | `Publish` job from `main` and release tags with `sha-<commit>` and version tags and labels, `Verify image` job that pulls the published image anonymously and checks it, and the manual proof that pull requests do not publish | #211, #212, #213, #214 | README §11, [docker-build.md](../docker-build.md) "Versioning and image tags", [testing/us-24-manual-checks.md](../testing/us-24-manual-checks.md) |

Coursework and process work done during the sprint, outside the increment and the velocity: Lab 6 (#181, #183), Lab 5 correction (#195), Lab 7 report (#218), sprint planning record (#185), architecture document (#193) and this review (#186).

**Evidence shown in the review** (README §8.3):

| Evidence | Where |
| --- | --- |
| Container startup | `docker compose ps` (db healthy, migrate exited 0, app running) and `/health`; container smoke tests in every `Container` job |
| Login for each role and denied access | Live demonstration (§4); end-to-end tests `tests/e2e/test_login_navigation.py` |
| A successful pipeline run | Run 43023718453 on `main` at `4c1e068`: `Lint`, `Tests`, `E2E`, `Container`, `Publish` and `Verify image` passed |
| A failed-check example | Test pull request #209, blocked by failed required checks ([evidence](../testing/us-23-evidence/)); deliberate-failure run 42389719199 with Playwright artifacts |
| A published image linked to its commit | `ghcr.io/ceciliagalvaoo/hospital-devops:sha-4c1e068`, whose `revision` label is the full SHA of `4c1e068`; tags `main`, `sha-6b0482d`, `sha-4fcbce3`, `sha-d1d025c`, `sha-5f03591` and `sha-4c1e068` in the registry |
| Test results | Default run: 179 passed and 1 skipped with 100 % line and branch coverage of `app/`; 9 end-to-end, 6 smoke and 7 published-image tests passing in CI |

## 4. Sprint Review

Held on 2026-11-14. The application was demonstrated on 2026-11-12 to a classmate who knows Git and Docker from the course and had never seen the project (about 25 minutes: 15 minutes following the review evidence of README §8.3, 10 minutes of free exploration), on the developer's computer in Chrome on Windows 11, with the Docker Compose stack at `5f03591` and the seeded development accounts.

### 4.1 Stories

| Story | Points | Acceptance criteria and Definition of Done | Result |
| --- | --- | --- | --- |
| US-22 Containerised application and database | 5 | All met | Accepted, closed |
| US-01 Login and role-based access | 8 | All met; defect #222 (below) does not affect an acceptance criterion, because the session is ended on the server | Accepted, closed |
| US-23 Continuous integration and merge checks | 8 | All met | Accepted, closed |
| US-24 Automated container publication | 5 | All met | Accepted, closed |

**Velocity:** 26 of 26 forecast points (README §8.1). No work returns to the backlog, and no story is re-estimated. The measured velocity of 26 points is the capacity reference for Sprint 2, whose plan is 23 points (README §8.4).

### 4.2 Demonstration and feedback

Each item of the review evidence worked in the demonstration. The classmate's feedback, in summary:

- **Clear:** the navigation changes with the role and explains the permissions on its own; the same message for a wrong password and an unknown login was recognised as deliberate; the "Access denied" page keeps the navigation; the merge stays blocked even for the administrator; the `revision` label links the image to its commit; the pages work on a small screen and with the keyboard.
- **Confusing:** the migration container shown as *Exited (0)*; the placeholder text naming user-story IDs ("delivered by US-03, US-09, …"); a login typed with a capital letter (`Dev.Doctor`) refused with the generic message; "Access denied" not saying which role has access; the *Latest* badge on the package page (GitHub's label for the newest version, not the image tag `latest`); the length of the `docker image inspect` command.
- **Missing:** the hospital functions themselves (patients, appointments), and password recovery.
- **Overall:** 8/10 — "a solid base for a first sprint: login, permissions and pipeline; what is missing is the system doing hospital things".

### 4.3 Backlog changes

| Finding | Decision |
| --- | --- |
| After logging out, the browser's **Back** button shows the previous page with the account name (no `Cache-Control: no-store`) | Defect **#222** (T-01.12, P0) in Sprint 2 |
| Swagger UI at `/docs` is reachable without login | To decide in the Sprint 2 planning (#187) |
| Logins are case-sensitive, and the interface does not say so | To decide in the Sprint 2 planning (#187) |
| Placeholder pages name user-story IDs | Wording to decide in the Sprint 2 planning (#187) |
| "Access denied" does not say who has access | Optional improvement, noted for the Sprint 2 planning (#187) |
| No password recovery | Out of scope: accounts are managed by the administrator (US-14, US-15) |
| The interface is in English | To decide in the Sprint 2 planning (#187) |

The Lab 7 Task 6 issues (#216, #217, #219) were moved to Sprint 2 on 2026-11-11.

## 5. Sprint Retrospective

Held on 2026-11-14, after the review.

**What went well**

- The 26 forecast points were done on 2026-11-07, seven days before the end of the sprint, working one task at a time through the full cycle.
- The tests found two defects before they reached a user (#202 at 320 px, #204 in the error-page titles), and a deliberate mutation check in almost every task showed that the tests fail when the behaviour breaks.
- CI with four required checks and the traceable, verified publication to GHCR were in place by the end of the sprint, as planned in §1.5.

**What went badly**

- The Sprint 1 iteration in the GitHub Project was configured with 30 days instead of two weeks, and was corrected only on 2026-11-07.
- The format of the pull-request titles and descriptions drifted from the established pattern in #184 and #194, and the PR texts needed corrections.
- The four stories were moved to *In Review* although no pull request was open, and the *In Progress* limit was exceeded, because README §10.4 did not say what the WIP limits count. Fixed with the rule in §10.4 and a filtered Kanban view.
- A wrong CI run number was written in four story comments and corrected afterwards; a network error produced a duplicate issue (#220).

**Blockers:** none stopped the work.

**Branching strategy** (review promised in `docs/branching-strategy.md` §1): **kept**. Task branches lived less than a day and never needed a conflict resolution, and the four required checks already validate every merge into `main`. The decision is reviewed again if work runs in parallel or branches start to live longer.

**Improvement action for Sprint 2:** before changing the board and before opening a pull request, check a short list: the status matches README §10.4 and the WIP limits; the pull-request title and description follow the pattern of the task type; every run number, issue number and link written in a comment or description is copied from its source, not from memory. The result is checked in the Sprint 2 retrospective (#188).
