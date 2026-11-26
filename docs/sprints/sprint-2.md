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
  - #40 T-09.3, the acceptance and access tests of US-09: 47 tests, each case through the API and the page (matching names and record numbers, inactive patients, empty and too short queries, no matches, doctors refused, no session, deactivated account), mapped in `docs/testing/us-09-automated-tests.md`; six faults in the application code each fail them. One test registers a patient on the page and finds it by search, which covers the open criterion of US-03. The test counts given in the description of #246 were wrong (14 unit and 19 integration tests; in fact 16 and 17); the map has the correct numbers.
  - #41 T-09.4, the end-to-end test of US-09: two patients registered through the form, searched by name and by record number, the correct record opened, the empty state and the query message, for receptionists and administrators; doctors refused. A mutation where every result linked to the first patient survived the first version, which clicked a name only when one patient was listed; the test now opens the second of two. The new module first had the same file name as an integration test module, which stops pytest from collecting either when both run; the full local run caught it before the commit and the module was renamed `test_search_and_open_patient.py`. The login and patient-name helpers of the end-to-end tests are shared. With it, US-03 and US-09 have every task done.
  - US-03 (3 points) and US-09 (2 points) closed after every criterion was checked, with the image `sha-9087ee7` (`0.3.0-dev.103`) published and verified. US-10's tasks were moved from Backlog: #43 in progress, #44–#46 ready.
  - #43 T-10.1, contact updates: `POST /api/patients/<id>/contacts` for receptionists and administrators replaces the phone and e-mail with the same format rules as registration, now shared in one function; a blank field removes the contact, invalid data changes nothing (HTTP 422), unknown patients return HTTP 404 and doctors HTTP 403.
  - #44 T-10.2, the contact-edit form `/patients/<id>/contacts`, filled in with the current contacts, and the confirmation "Contact details saved." on the record, which links to the form; the form macros are shared with registration. The CSRF inventory test of US-01 read only `app/routes/pages.py`, so `POST /patients/new` (#33) had never been listed; it now reads every route hidden from the API schema, and both patient form routes are listed. At 320 px the record broke its date of birth in the middle; record numbers and dates no longer wrap.
  - #45 T-10.3, the acceptance and access tests of US-10: 28 tests, each case through the API and the page (valid updates persisted and shown on the reloaded record, an empty contact removed, invalid phones and e-mails identified without changing anything, doctors refused, no session, deactivated account, unknown patient), mapped in `docs/testing/us-10-automated-tests.md`; five faults in the application code each fail them.
  - #46 T-10.4, the end-to-end test of US-10 in Chromium: from the record to the contact form filled in with the current contacts, an invalid e-mail identified without saving, a new phone and an emptied e-mail saved with the confirmation, the record reloaded and reopened with the new values, for receptionists and administrators; doctors refused. Five faults each fail it, including an update that is never written to the database. With it, every task of US-10 and of week 1 is done.
- **Next:** close US-10; week 2 starts with US-02 (#55–#60), registering a doctor.
- **Blockers:** none. A local dry run showed that `imagetools create` from an image pushed by Docker wraps it in an index with a new digest; the image is therefore pushed under an upload name first, and every name is created from that index. The first CI run of the pull request failed in `Container`: `--pull never` also applied to the PostgreSQL image, which a clean runner does not have; the local-image mode now relies on `pull_policy: never` for the application only, verified locally after removing the PostgreSQL image.

### 2026-11-26

- **Done:**
  - US-10 (2 points) closed on 2026-11-18 after every criterion was checked, with the image `sha-c062e8d` (`0.3.0-dev.111`) published and verified; week 1 ended with 7 of 23 points and every planned item done.
  - No work was done from 2026-11-19 to 2026-11-25, so week 2 starts today with 16 points and 21 pull requests left before the review on 2026-11-28. The Product Owner kept the sprint scope and set the order by value: US-02 (P1), then the Lab 7 tasks #217 and #219, then US-14, US-13 and US-15. Whatever is not done by the review returns to the backlog there.
  - #55 T-02.1, the `doctors` and `doctor_availability` tables (migration `0005`). The Product Owner decided the open points of the doctor stories: a doctor profile is linked to an existing doctor account (one per account), the specialisation comes from a fixed list, and the availability is a set of weekly ranges (weekday, start and end time).
  - #56 T-02.2, doctor registration: `POST /api/doctors` for administrators (receptionists and doctors HTTP 403). The account must be an active doctor account without a profile; the name and a specialisation from the list are required; the availability needs at least one weekly range on the half hour, with the end after the start and no overlap on the same day, and each invalid range is reported by its row, in row order.
  - #57 T-02.3, the doctors area `/doctors` (list and registration link), the form `/doctors/new` with the eligible accounts, the specialisation list and six availability rows, each showing its own error, and the profile `/doctors/<id>` with the weekly availability and the confirmation. Checked in Chromium at 1000 px and 320 px; the screenshots showed "Wednesday" cut in the weekday select, and the weekday column was widened.
  - #58 T-02.4, the acceptance and access tests of US-02: 41 tests, each case through the API and the page (a doctor saved active and linked to the doctor account with its ranges, ineligible and already linked accounts refused, missing details and five kinds of invalid ranges identified by row, adjacent ranges accepted, receptionists and doctors refused, no session, deactivated administrator), mapped in `docs/testing/us-02-automated-tests.md`; six faults in the application code each fail them.
  - #59 T-02.5, the end-to-end test of US-02 in Chromium: an administrator opens the form from the navigation, submits it with no specialisation and an overlap (both identified, the overlap on its row), corrects it, sees the profile with the confirmation and the weekly ranges, finds the doctor in the list and opens the same profile, and the account is no longer offered; receptionists and doctors have no Doctors link and are refused. A fault where every list entry linked to the first doctor survived, because the end-to-end database holds one doctor; the page test of the list now checks the link of each of two doctors.
  - #60 T-02.6, the manual checks of the doctor form in Chrome 158 on Windows 11: labels of the details and the availability rows, the wording of every validation message, keyboard use, a valid registration and the receptionist's refusal; 19 of 19 pass, no defect. The application's request log was used to confirm each submission, and the label and keyboard checks were repeated in headless Chromium. With it, every task of US-02 is done.
  - US-02 (5 points) closed after every criterion was checked, with the image `sha-c03e95b` (`0.3.0-dev.123`) published and verified (built from the commit that is `8edb786` since the history rewrite below); the sprint has 12 of 23 points done.
  - #217 LAB7-06b, black-box journeys against the running container, in the `Container` job and so against the image that `Publish` pushes (the build-once part of the issue was delivered by #228): each role logs in, sees exactly its areas, logs out and loses its session, and the front desk registers and finds a patient while a doctor is refused. JUnit reports of `Tests`, `E2E` and `Container` are uploaded on every run. Run against images with a fault, the journeys fail when a doctor may open the patients page, when a wrong password is accepted and when search finds nothing; a first fault, in the navigation table, changed no behaviour the journeys can see, because the patients page has its own role check since #39.
  - #217 verified on `main`: run 45818801814 published `sha-a2497bc` (the commit is `7b4e376` since the history rewrite below) with the same image ID as the image the `Container` job built and tested (`sha256:c7d1f172…`), and `Verify image` passed.
  - #219 LAB7-06c, the test plan `docs/testing.md`: the five test types and where they run, the tests of all 26 user stories (the files of the delivered ones, the planned test tasks of the others, and a reason for every type a story does not use), the pipeline and why its checks run in parallel, the thresholds, the failed and fixed run of #234, and why the tests use a PostgreSQL service container instead of Testcontainers.
  - #15 T-14.1, staff account creation: `POST /api/staff` for administrators (receptionists and doctors HTTP 403), with a unique login, one of the three roles and a password of 12 characters to 72 bytes stored as a bcrypt hash. Logins are now stored and compared in lower case, at creation and at login, as decided after the Sprint 1 review, so a duplicate in another case is refused and `NIGHT.SHIFT` logs in as `night.shift`. The minimum of 12 characters is a design choice, not a requirement; the Product Owner can change it.
  - #16 T-14.2, the staff accounts area `/staff` (account list and creation link) and the form `/staff/new` with the password asked twice; after an error the login and role are kept and the passwords are never sent back, and the password fields use `autocomplete="new-password"`, now a parameter of the shared field macro (it had been fixed to `off`).
  - #17 T-14.3, the acceptance and access tests of US-14: 41 tests, each case through the API and the page (a bcrypt hash with cost 12 and a login with the assigned role for each role, the new account's areas, duplicates in any case, unsupported roles, invalid logins and passwords, receptionists and doctors refused, no session, deactivated administrator), mapped in `docs/testing/us-14-automated-tests.md`; five faults in the application code each fail them, including a weaker bcrypt cost.
  - The history of `main` from #55 on was rewritten to remove a co-author trailer that the Product Owner did not want in the commit messages and that listed an extra contributor on GitHub. Only the messages of the three commits of #55 changed; the 34 commits from #55 on got new hashes, with the same content, authors and dates (checked commit by commit, after a rehearsal on a throw-away clone). The ruleset of `main` was disabled for the force push only and re-enabled with the same rules, and CI run 45833311471 passed on the rewritten `main` (`d6a9954`). Short hashes cited in the documentation and in two issue comments were updated; published image tags keep their names. The tester line of the US-24 manual checks was reworded to name only the tester.
  - #18 T-14.4, the end-to-end test of US-14 in Chromium: an administrator creates an account from the navigation (first with passwords that do not match, which are not sent back), sees it highlighted in the list, logs out, and the new account logs in with its login typed in capitals and sees exactly the doctor's areas; receptionists and doctors are refused. The test plan `docs/testing.md` now lists the US-14 test files. With it, every task of US-14 is done.
  - US-14 (5 points) closed after every criterion was checked, with the image `sha-8eae52c` (`0.3.0-dev.136`) published and verified; the sprint has 17 of 23 points done.
  - #62 T-13.1, doctor updates: `POST /api/doctors/<id>` for administrators (receptionists and doctors HTTP 403, even for their own profile) changes the name, the specialisation and the weekly availability with the rules of registration, now shared in one function; the new ranges replace the old ones, and the account link and the status are kept. US-13's first criterion also says that existing appointments are retained: appointments do not exist yet (US-04, Sprint 3); the update changes only the profile and its ranges and deletes nothing that refers to the doctor, and the retention of appointments is to be checked when US-04 is integrated.
  - #63 T-13.2, the doctor-edit form: "Edit doctor details" on the profile opens `/doctors/<id>/edit` with the current name, specialisation and ranges; the staff account is shown but cannot be changed. Errors keep the submitted values and identify each field and row, as in registration (the availability rows are now one template macro shared by both forms); a saved change returns to the profile with "Doctor details saved." Checked in Chromium against a running stack at 1000 px and 320 px (no horizontal scroll).
  - #64 T-13.3, the acceptance and access tests of US-13: 43 tests, each case through the API and the edit page, mapped in `docs/testing/us-13-automated-tests.md`. For the retention of appointments, which do not exist yet, they check that an update keeps the doctor's id, account link and status and changes no other doctor. Six faults each fail them, among them an update that reactivates an inactive doctor and the API taking the account from the form.
- **Next:** #65 T-13.4, the end-to-end test of updating and reloading doctor details.
- **Blockers:** none. The local test environment had been removed with the session's temporary files and was recreated from `requirements-dev.txt`.

## 3. Increment

To be completed in the Sprint Review (#188).

## 4. Sprint Review

To be completed on 2026-11-28 (#188).

## 5. Sprint Retrospective

To be completed on 2026-11-28 (#188).
