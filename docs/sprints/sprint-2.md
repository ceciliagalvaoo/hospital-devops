# Sprint 2 — Registration and administration

| | |
| --- | --- |
| Dates | 2026-11-15 to 2026-11-28 (two weeks) |
| Goal | Deliver patient and doctor registration and administrative account management |
| Planned stories | US-03, US-09, US-10, US-02, US-13, US-14, US-15 (23 points) |
| Planning | Held and recorded on 2026-11-15 (#187) |
| Review and retrospective | 2026-11-28 (#188) |
| Release | `v0.3.0` (#188) |

This file is the record of the sprint ceremonies required by [planning.md](../planning.md) §1.3: the planning, the work log that replaces the Daily Scrum, and the review and retrospective. The pull request of each task adds its own work-log entry.

## 1. Sprint Planning

### 1.1 Goal and selected stories

The goal and the stories come from the projected sprint backlog in [planning.md](../planning.md) §2.4.

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

**Refinement** ([planning.md](../planning.md) §1.4 and [estimation.md](../estimation.md) §6): every story has acceptance criteria in [backlog.md](../backlog.md) §3; none is larger than 5 points, so no story needs splitting (13-point stories are split and 8-point stories examined); the dependencies on US-01 and US-22 are satisfied by Sprint 1. All selected stories and their 32 tasks are assigned to Sprint 2 in the GitHub Project. The *Done when* conditions of each task are refined when the task starts, as in Sprint 1.

### 1.2 Capacity

Sprint 1 measured a velocity of **26 points** (`docs/sprints/sprint-1.md` §4.1), which replaces the opening forecast ([planning.md](../planning.md) §2.1). The 23 planned points fit within it. The sprint also contains work without points: two defects, one implementation task from the review, one documentation task, three Lab 7 tasks and the two ceremony tasks. If the capacity is not enough, the P2 stories US-13, US-14 and US-15 are deferred first ([planning.md](../planning.md) §2.1); the P1 stories and the defects are not deferred.

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

Dependencies were checked against [tasks.md](../tasks.md). Tasks are worked one at a time through the full cycle, and each task is refined when it starts.

1. #187 — this planning (closes on 2026-11-15).
2. Defects and review follow-up: #222, #224, #225 — small changes that fix what is already published.
3. #216 — the coverage gate, before new code is added.
4. #169 — DOC-01, early on purpose: it moves README sections into `docs/`, and every later task edits the documentation; doing it last would conflict with all of them.
5. Patients: US-03 (#31 → #32 → #33 → #34 → #35 → #36), then US-09 (#38 → #39 → #40 → #41) and US-10 (#43 → #44 → #45 → #46). US-03 and US-09 are completed in the same sprint so that the registration criterion involving search can be verified ([planning.md](../planning.md) §2.4).
6. Doctors: US-02 (#55 → #56 → #57 → #58 → #59 → #60), then US-13 (#62 → #63 → #64 → #65).
7. Staff accounts: US-14 (#15 → #16 → #17 → #18), then US-15 (#20 → #21 → #22 → #23).
8. #217 — test and publish the same image, with the black-box journey.
9. #219 — the test plan, at the end, so that it includes the tests of this sprint.
10. #188 — review, retrospective and release `v0.3.0` on 2026-11-28.

At the planning, the unblocked items #222, #224, #225, #216, #169, #31 (T-03.1), #55 (T-02.1), #15 (T-14.1) and #217 were moved to *Ready* ([github-project.md](../github-project.md) §4).

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

- **Review evidence** ([planning.md](../planning.md) §2.4): demonstrate registration, search, updates, account creation and deactivation, including denied actions for unauthorised roles.
- **Retrospective action from Sprint 1:** before changing the board and before opening a pull request, check that the status matches [github-project.md](../github-project.md) §4 and the WIP limits, that the pull-request text follows the pattern of the task type, and that every run number, issue number and link is copied from its source. The result is checked in the Sprint 2 retrospective (#188).

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
  - #229, the first promoted release: `v0.2.1-rc.1` (pre-release) and `v0.2.1`, approved in `production`, both on f4bec54 with the digest of the tested dev image (Release runs 44290421084 and 44290895319); `docs/publishing.md` documents the registry, stages, credentials, consumption, revocation, withdrawal and clean-up.
  - #230, the Lab 8 report for Tasks 0–4 (`docs/publishing-lab.md` with 18 screenshots in `docs/lab8-evidence/`), checked against `testing-demo` and `publish-demo` (releases, environments, tag rulesets, digests) and for credentials.
  - #216, the coverage gate: `.coveragerc` requires 100 % of lines and branches of `app/`, locally and in CI. Before it, the `Tests` job did not measure branches at all. Shown locally with two deliberately uncovered changes, an unexecuted line and a branch never taken, which both fail the run while all tests pass. In CI, the throw-away pull request #237 added a branch that no test takes: `Tests` failed with "Required test coverage of 100.0% not reached. Total coverage: 99.80%" although all 223 tests passed (run 44298090581), and the merge was blocked; it was closed without merging.
  - #169 DOC-01, the documentation restructured: `README.md` keeps the overview, a quickstart and links; its sections moved unchanged into `docs/requirements.md`, `backlog.md`, `tasks.md`, `estimation.md`, `planning.md`, `tooling.md`, `github-project.md` and `docs/development/` (running locally, testing, CI, migrations, accounts and access control, branching strategy, Git workflow), with `docs/README.md` as the index, diagrams in `docs/diagrams/` and the Lab 4 and Lab 5 notes in `docs/labs/`. Every "README §X" reference was updated; all 207 relative links and images resolve. The Lab 6–8 reports stay where they are, because their links were already submitted.
  - #31 T-03.1, the `patients` table (migration `0004`): name and date of birth required, phone and e-mail optional, active flag. The Product Owner decided the two open points of the patient stories: the identifier for search is a record number derived from the id (`P-000042`), and no national document number is collected; the contact details are an optional phone and e-mail.
  - #32 T-03.2, patient registration: `POST /api/patients` for receptionists and administrators (doctors HTTP 403, no session HTTP 401), with the rules in `app/patients.py` shared with the coming page: name and a real date of birth between 1900 and today required, phone and e-mail optional but well formed, every invalid field reported with HTTP 422.
  - #33 T-03.3, the registration page `/patients/new` and the record page `/patients/<id>` with the confirmation: labels and required markers, an error summary linked to the fields, messages next to each field, the values kept and the focus on the first invalid field; after saving, a redirect to the record, so a reload never registers the patient twice. Checked in Chromium at 1000 px and 320 px without horizontal scrolling.
  - #34 T-03.4, the acceptance and access tests of US-03: 36 tests, each case through the API and the page (persistence, missing fields, invalid dates, doctors refused, no session, deactivated account), mapped to the criteria in `docs/testing/us-03-automated-tests.md`; six faults in the application code each fail them. The search part of the first criterion is verified with US-09.
  - #35 T-03.5, the end-to-end test of US-03 in Chromium: from the navigation to the form, the empty form rejected with both fields identified, the corrected form saved and the record displayed with its confirmation, for receptionists and administrators; doctors have no Patients link and are refused. The registration form joined the 320 px check. Without the redirect after saving, the browser's reload registered the patient twice, and the test caught it.
  - #36 T-03.6, the manual checks of the patient form in Chrome 157 on Windows 11: labels, validation messages, keyboard navigation, reload after saving and the doctor's refusal; 19 of 19 pass, no defect. The keyboard checks were repeated in headless Chromium with the same result. With it, every task of US-03 is done.
  - US-03 has every task done; it stays open until US-09 verifies its "can be found through patient search" criterion, as its note says. Nine of its eleven items are checked, with the evidence in the issue.
  - #38 T-09.1, patient search: `GET /api/patients?q=` for receptionists and administrators, by record number (`P-000042`, `P42`, `42`) or by every word of the name in any order, ignoring case, with `%` and `_` matched literally; ordered by name, at most 50 results with a `more` flag, inactive patients included. Search does not ignore accents yet (it needs the `unaccent` extension), recorded as a limitation.
  - #39 T-09.2, the patients area page: the registration link, the search form, the result table (linked names, inactive patients marked) and the empty state; an unusable query shows its message at the field. At 320 px the table broke words in the middle, because of the page-wide wrapping rule of defect #202; the table now wraps only at spaces and scrolls inside a keyboard-focusable region. A test assertion of mine that could never fail was found and corrected before the commit.
- **Next:** #40 T-09.3, the acceptance and access tests of US-09.
- **Blockers:** none. A local dry run showed that `imagetools create` from an image pushed by Docker wraps it in an index with a new digest; the image is therefore pushed under an upload name first, and every name is created from that index. The first CI run of the pull request failed in `Container`: `--pull never` also applied to the PostgreSQL image, which a clean runner does not have; the local-image mode now relies on `pull_policy: never` for the application only, verified locally after removing the PostgreSQL image.

## 3. Increment

To be completed in the Sprint Review (#188).

## 4. Sprint Review

To be completed on 2026-11-28 (#188).

## 5. Sprint Retrospective

To be completed on 2026-11-28 (#188).
