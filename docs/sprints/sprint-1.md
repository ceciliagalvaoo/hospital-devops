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
  - Lab 5: removed the outdated deferral note as #195 (PR #196).
  - This planning record (#185).
  - US-01: #13, CSRF protection for every state-changing request.
  - US-01: #9, login pages and role-based navigation, with placeholder area pages for the Sprint 1 review.
- **Next:** #10, automated authentication, session, CSRF and role-access tests.
- **Blockers:** none.

## 3. Increment

To be completed in the Sprint Review (#186).

## 4. Sprint Review

To be completed on 2026-11-14 (#186).

## 5. Sprint Retrospective

To be completed on 2026-11-14 (#186).
