# Project management on GitHub

## 1. GitHub Project

The backlog from [backlog.md](backlog.md) and [tasks.md](tasks.md) is tracked in the GitHub Project **Hospital DevOps**, linked to this repository:
<https://github.com/users/ceciliagalvaoo/projects/3>.

Every epic, user story and task is a GitHub Issue in this repository, assigned to the project owner. Backlog identifiers (E1, US-01, T-01.1) are kept at the start of every issue title and are different from GitHub issue numbers (#1, #3, #5). The project currently contains 6 epics, 26 user stories (including the three optional ones) and 142 tasks: the 127 backlog tasks from [tasks.md](tasks.md) and 15 standalone tasks for coursework (`LAB…`), documentation (`DOC-…`) and the sprint ceremonies (`SPRINTn-…`).

## 2. Labels and hierarchy

Each issue carries exactly one level label:

| Label | Level | Title format | Example |
| --- | --- | --- | --- |
| `epic` | Epic | `E<n> — <name>` | #1 E1 — Authentication and access |
| `user-story` | User story | `US-XX — <name>` | #3 US-01 — Login and role-based access |
| `task` | Task | `T-XX.Y — <short description>` | #5 T-01.1 — Create staff account model and migration |

- Test tasks are tagged in the title with `[TEST][auto]` (formal automated test) or `[TEST][manual]` (manual test case), for example #136 T-22.5 — [TEST][auto] Container startup, health and database smoke check. Searching issues for `[TEST]` lists all planned testing work.
- The additional label `optional` marks the optional stories US-19 to US-21.
- The hierarchy uses native sub-issues: **Epic → User story → Task**. Tasks are never attached directly to an epic. The *Parent issue* and *Sub-issues progress* columns show the tree and the progress of each story.
- New issues are created from the templates in `.github/ISSUE_TEMPLATE/`: `epic.md`, `user-story.md`, `task.md` and `defect.md`. `config.yml` disables blank issues, so every new issue follows one of these templates.
- Defects found during testing are task-level issues: they carry the `task` level label plus the `defect` label, are titled `T-XX.Y — [DEFECT] <description>`, are added as sub-issues of the affected user story and use Item type = defect. They receive no Story points.

## 3. Project fields

| Field | Type | Epics | User stories | Tasks |
| --- | --- | --- | --- | --- |
| Story points | Number | Empty | Estimate from [estimation.md](estimation.md) §4 | Empty (stories are estimated, not tasks) |
| Priority | Single select: P0 — Critical, P1 — High, P2 — Medium, P3 — Low | Empty | See rule below | Inherited from the parent story |
| Sprint | Iteration, two weeks | Empty (epics span several sprints) | Sprint from [planning.md](planning.md) §2.2 | Inherited from the parent story |
| Epic | Single select: E1 to E6 | Own epic | Parent epic | Epic of the parent story |
| Item type | Single select: epic, story, task, defect | epic | story | task |

Priority describes how soon a story is needed, independently of its size:

- **P0 — Critical:** Sprint 1 foundation that every other story depends on (US-22, US-01, US-23, US-24).
- **P1 — High:** required stories that are never deferred or are not in the deferral list of [planning.md](planning.md) §2.1 (US-02 to US-10, US-12, US-16, US-17, US-25, US-26).
- **P2 — Medium:** required stories that are deferred first if velocity is insufficient (US-11, US-13, US-14, US-15, US-18).
- **P3 — Low:** optional stories (US-19, US-20, US-21).

The optional stories US-19 to US-21 are intentionally left **without a sprint**. They stay in the backlog, outside the 102-point baseline, and are not artificially placed in one of the four sprints ([planning.md](planning.md) §2.7).

The Sprint iterations are Sprint 1 (1 Nov 2026), Sprint 2 (15 Nov), Sprint 3 (29 Nov) and Sprint 4 (13 Dec), each lasting 14 days, so the last sprint ends on 26 Dec 2026. The per-sprint sums in the *Sprint plan* view were cross-checked against [planning.md](planning.md) §2.2 and match: Sprint 1 = 26, Sprint 2 = 23, Sprint 3 = 24, Sprint 4 = 29 (102 required points), plus 6 optional points with no sprint.

## 4. Status workflow and WIP limits

| Status | Meaning | Column limit |
| --- | --- | --- |
| Backlog | Not yet planned into the current sprint, or still blocked | None |
| Ready | In the current sprint and not blocked | None |
| In Progress | A linked branch exists for it | 2 |
| In Review | A pull request is open | 2 |
| Done | Merged, and the Definition of Done is ticked | None |

The limits are lower than the course suggestion because this is an individual project. GitHub shows a warning but does not enforce them, so they are respected by convention. Blocked items are never moved to Ready.

The limits of *In Progress* and *In Review* count **tasks and defects only**. User stories never enter *In Review*, which is reserved for open pull requests: a story is *In Progress* from its first started task until it is accepted in the Sprint Review, and then *Done*. This rule was added on 2026-11-07, when the four Sprint 1 stories exceeded the *In Progress* limit while waiting for the review (`docs/sprints/sprint-1.md` §5).

## 5. Views

| View | Layout | Configuration | Question it answers |
| --- | --- | --- | --- |
| Backlog | Table | All items, with Parent issue, Sub-issues progress, Story points, Priority, Epic, Item type and Sprint | Is every item in the tree, with its fields? |
| Backlog by priority | Table | Filter `label:user-story`, sorted by Priority; shows Story points, Priority, Sprint and Epic | What matters most, regardless of when? |
| Sprint plan | Table | Filter `label:user-story`, grouped by Sprint, with the Story points sum per group | Is each sprint deliverable, and does it match [planning.md](planning.md) §2.2? |
| Kanban – Sprint | Board | Columns by Status, filter `sprint:@current -label:user-story`; cards show Priority, assignees and labels | What are the tasks and defects of the current sprint doing, within the WIP limits? |

Only user stories are counted in the planning views, so task rows do not duplicate the story-point sums; the *Kanban – Sprint* view shows only tasks and defects, so its columns match the WIP limits of §4, and the stories of the sprint are followed in the *Sprint plan* view. The Kanban board stays empty until the current date falls inside a Sprint iteration; before that, the *Backlog* view is used.

## 6. Automation

The project workflows are:

- **Auto-add to project:** new open issues from `hospital-devops` (`is:issue is:open`) are added automatically.
- **Item added to project** → Status `Backlog`.
- **Item closed** → Status `Done`.
- **Pull request merged** → Status `Done`.

Ready, In Progress and In Review are moved by hand. Closing a duplicate issue as *not planned* is not treated as completed work.

## 7. Branch naming convention

```text
<issue-number>-<task-id>-<short-description>
```

- The issue number comes first so that automation can parse it.
- The task identifier is written in lower case with dots replaced by hyphens (`T-22.1` → `t-22-1`).
- One branch per task (or per small user story), always created from an up-to-date `main`.
- Changes are never committed directly to `main`.

Examples using real issues:

```text
132-t-22-1-fastapi-health-endpoint     # #132 T-22.1 — Create FastAPI application structure and health endpoint
133-t-22-2-dockerfile-non-root-user    # #133 T-22.2 — Create Dockerfile with a non-root runtime user
75-t-04-2-booking-conflict-validator   # #75  T-04.2 — Implement availability and booking-conflict validator
```

**1. Create the branch linked to the issue.** Open the issue, find **Development** in the right sidebar, click **Create a branch**, set the name according to the convention and choose `main` as the source. The terminal alternative creates and links the branch in one step:

```bash
gh issue develop 132 --name 132-t-22-1-fastapi-health-endpoint --base main --checkout
gh issue develop --list 132   # lists the branches linked to issue #132
```

A branch created only with `git checkout -b` and pushed manually is **not** linked to the issue.

**2. Fetch the branch and switch to it locally.**

```bash
git fetch origin
git switch 132-t-22-1-fastapi-health-endpoint   # tracks origin/132-t-22-1-fastapi-health-endpoint
```

**3. Reference the issue in commits**, so that each commit appears on the issue timeline:

```bash
git add requirements.txt app/__init__.py app/main.py app/routes/__init__.py app/routes/health.py
git commit -m "feat: create FastAPI application structure and health endpoint (#132)"
git push
```

**4. Open a pull request into `main`.** The description references the work item and uses a closing keyword once the implementation satisfies the task's *Done when* conditions:

```text
Closes #132
```

Merging the pull request closes the issue automatically, and the project workflow moves it to Done. `Closes` is only used when the change completes the issue; partial work uses `Refs #132` instead.

## 8. Dependencies

The "Blocked by" relationships from [tasks.md](tasks.md) are registered natively through **Relationships → Mark as blocked by**, at both story and task level, including the cross-story task dependencies stated explicitly in [tasks.md](tasks.md) (for example, #5 T-01.1 is blocked by T-22.4). Issue descriptions repeat them as `#N` references. Parent/child relationships are not registered as dependencies.

Useful filters, both in the project and in the repository Issues tab:

```text
is:blocked
is:blocking
blocked-by:131
blocking:131
```

From the terminal:

```bash
gh issue view 133 --json blockedBy,blocking
gh issue edit 133 --add-blocked-by 132
```
