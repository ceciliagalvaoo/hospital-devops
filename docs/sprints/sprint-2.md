# Sprint 2 — Registration and administration

| | |
| --- | --- |
| Dates | 2026-11-15 to 2026-11-28 (two weeks) |
| Goal | Deliver patient and doctor registration and administrative account management |
| Planned stories | US-03, US-09, US-10, US-02, US-13, US-14, US-15 (23 points) |
| Planning | Held and recorded on 2026-11-15 (#187) |
| Review and retrospective | 2026-11-28 (#188) |
| Release | `v0.3.0` (#188) |

This file is the record of the sprint ceremonies required by README §5.3: the planning, the work log that replaces the Daily Scrum, and the review and retrospective. The pull request of each task adds its own work-log entry.

## 1. Sprint Planning

### 1.1 Goal and selected stories

The goal and the stories come from the projected sprint backlog in README §8.4.

| Story | Issue | Deliverable | Points | Priority |
| --- | --- | --- | --- | --- |
| US-03 | #30 | Register patients | 3 | P1 |
| US-09 | #37 | Search for patients | 2 | P1 |
| US-10 | #42 | Edit patient contact details | 2 | P1 |
| US-02 | #54 | Register doctors with specialisation and availability | 5 | P1 |
| US-13 | #61 | Update doctor details and availability | 3 | P2 |
| US-14 | #14 | Create staff accounts and assign roles | 5 | P2 |
| US-15 | #19 | Deactivate staff accounts and reject subsequent access | 3 | P2 |
| **Total** | | | **23** | |

**Refinement** (README §5.4 and §7.6): every story has acceptance criteria in README §4.3; none is larger than 5 points, so no story needs splitting (13-point stories are split and 8-point stories examined); the dependencies on US-01 and US-22 are satisfied by Sprint 1. All selected stories and their 32 tasks are assigned to Sprint 2 in the GitHub Project. The *Done when* conditions of each task are refined when the task starts, as in Sprint 1.

### 1.2 Capacity

Sprint 1 measured a velocity of **26 points** (`docs/sprints/sprint-1.md` §4.1), which replaces the opening forecast (README §8.1). The 23 planned points fit within it. The sprint also contains work without points: two defects, one implementation task from the review, one documentation task, three Lab 7 tasks and the two ceremony tasks. If the capacity is not enough, the P2 stories US-13, US-14 and US-15 are deferred first (README §8.1); the P1 stories and the defects are not deferred.

### 1.3 Work without story points

| Item | Issue | Why it is in this sprint |
| --- | --- | --- |
| T-01.12 — [DEFECT] Back button shows the previous page after logout | #222 | Found in the Sprint 1 Review (P0) |
| T-24.5 — [DEFECT] Release tag overwrites the commit tag of the main image | #224 | Found with the release `v0.2.0` (P0) |
| T-01.13 — Expose the API documentation only in development | #225 | Decision of this planning (§1.5) |
| LAB7-06a — Coverage quality gate | #216 | Lab 7, Task 6 (moved to Sprint 2 on 2026-11-11) |
| LAB7-06b — Test and publish the same image, black-box end-to-end journey | #217 | Lab 7, Task 6 |
| LAB7-06c — Test plan of the project | #219 | Lab 7, Task 6 |
| DOC-01 — Restructure project documentation | #169 | Planned for the start of Sprint 2 |
| SPRINT2-01 — Planning and work log | #187 | Ceremony (this record) |
| SPRINT2-02 — Review, retrospective and release `v0.3.0` | #188 | Ceremony |

### 1.4 Task sequence

Dependencies were checked against README §6. Tasks are worked one at a time through the full cycle, and each task is refined when it starts.

1. #187 — this planning (closes on 2026-11-15).
2. Defects and review follow-up: #222, #224, #225 — small changes that fix what is already published.
3. #216 — the coverage gate, before new code is added.
4. #169 — DOC-01, early on purpose: it moves README sections into `docs/`, and every later task edits the documentation; doing it last would conflict with all of them.
5. Patients: US-03 (#31 → #32 → #33 → #34 → #35 → #36), then US-09 (#38 → #39 → #40 → #41) and US-10 (#43 → #44 → #45 → #46). US-03 and US-09 are completed in the same sprint so that the registration criterion involving search can be verified (README §8.4).
6. Doctors: US-02 (#55 → #56 → #57 → #58 → #59 → #60), then US-13 (#62 → #63 → #64 → #65).
7. Staff accounts: US-14 (#15 → #16 → #17 → #18), then US-15 (#20 → #21 → #22 → #23).
8. #217 — test and publish the same image, with the black-box journey.
9. #219 — the test plan, at the end, so that it includes the tests of this sprint.
10. #188 — review, retrospective and release `v0.3.0` on 2026-11-28.

At the planning, the unblocked items #222, #224, #225, #216, #169, #31 (T-03.1), #55 (T-02.1), #15 (T-14.1) and #217 were moved to *Ready* (README §10.4).

### 1.5 Decisions

Decisions on the findings of the Sprint 1 Review (`docs/sprints/sprint-1.md` §4.3):

| Finding | Decision | Where |
| --- | --- | --- |
| Swagger UI at `/docs` reachable without login | The API documentation exists only with `APP_ENV=development`; the published image does not serve it | #225 |
| Logins are case-sensitive, and the interface does not say so | Logins are normalised to lower case when an account is created and when a user logs in | US-14, T-14.1 (#15) |
| Placeholder pages name user-story IDs | Neutral wording ("This area will be available in a later version.") | T-03.3 (#33) |
| "Access denied" does not say who has access | Kept generic: simpler, and it does not expose the role structure | — |
| The interface is in English | Kept in English, consistent with the code, the documentation and the course | — |

Other decisions:

- **Review evidence** (README §8.4): demonstrate registration, search, updates, account creation and deactivation, including denied actions for unauthorised roles.
- **Retrospective action from Sprint 1:** before changing the board and before opening a pull request, check that the status matches README §10.4 and the WIP limits, that the pull-request text follows the pattern of the task type, and that every run number, issue number and link is copied from its source. The result is checked in the Sprint 2 retrospective (#188).

## 2. Work log

Each entry records the completed work, the next action and any blockers.

### 2026-11-15

- **Done:** Sprint Planning (§1): stories, capacity, sequence and decisions; task #225 created from the review feedback; unblocked items moved to *Ready*.
- **Next:** #222, the Back-button defect.
- **Blockers:** none.

### 2026-11-17

- **Done:** Lab 8 (publishing, versioning and registries) planned: Task 5 in this project as #227 (versioning and channels), #228 (build once and promote, with environments; it also fixes #224) and #229 (release `v0.2.1-rc.1` → `v0.2.1` and `docs/publishing.md`), and the report of Tasks 0–4 as #230. `v0.2.1` replaces the lab's `v0.1.0`, which already exists. The moving tag `dev` replaces `main`. The build-once part of #217 moved to #228.
- **Next:** the sequence of §1.4 changes to #222 → #225 → #227 → #228 → #229 → #216 → #169 → the stories → #217 → #219 → #188. Week 1 (until 2026-11-21): the defects, Lab 8, #216, #169 and the patient stories; week 2: the doctor and staff-account stories, #217, #219 and #188.
- **Blockers:** none. Correction: §1.1 said 33 story tasks; the project has 32.

### 2026-11-18

- **Done:**
  - #222, every response except the static files is sent with `Cache-Control: no-store`, so Back after logout shows the login page.
  - #225, the API documentation (`/docs`, `/redoc`, `/openapi.json`) is served only with `APP_ENV=development`; the published image returns HTTP 404 for it. The application is now created by `create_app()`.
  - #227, `docs/versioning.md` (scheme, channels, tag format, mutable and immutable names, who may release) and the version script with the channels `dev` (`X.Y.Z-dev.N` from `main`), `rc` and `release`, rejecting malformed tags and keeping `X.Y.Z-dev.*` after a release candidate.
  - #228, the image is built once and promoted: `Container` builds and smoke-tests it, `Publish` pushes that same image as `sha-<commit>`, `X.Y.Z-dev.N` and `dev`, and the new release workflow promotes it to rc or release names without building, after the approval of the new `production` environment, and creates the GitHub Release. This also fixes #224.
- **Next:** #229, release `v0.2.1-rc.1` and `v0.2.1` and `docs/publishing.md`.
- **Blockers:** none. A local dry run showed that `imagetools create` from an image pushed by Docker wraps it in an index with a new digest; the image is therefore pushed under an upload name first, and every name is created from that index.

## 3. Increment

To be completed in the Sprint Review (#188).

## 4. Sprint Review

To be completed on 2026-11-28 (#188).

## 5. Sprint Retrospective

To be completed on 2026-11-28 (#188).
