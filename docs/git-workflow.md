# Git workflow

This document records the Git workflow used in this repository. It was practised in Lab 4 (#162) and applied end to end to a real backlog task, #132 (T-22.1 — Create FastAPI application structure and health endpoint).

Evidence is labelled by source:

- **Verified:** checked against the repository history, the local repository state while the work was done, the remote refs or the GitHub API (commits, pull requests, issue events, tags, release and ruleset).
- **Reported:** practice confirmed by the author that leaves no trace in the history, such as local commands, terminal output or the project board.

## 1. Branch convention

Task branches follow the convention defined in README §10.7:

```text
<issue-number>-<task-id>-<short-description>
```

- The issue number comes first; the task identifier is lower case with dots replaced by hyphens (`T-22.1` → `t-22-1`).
- Example: `132-t-22-1-fastapi-health-endpoint` for #132.
- The branch is created from the issue (**Development → Create a branch**) or with `gh issue develop`, so that it is linked to the issue.
- Lab 4 practice branches use the `lab4/<topic>` prefix, for example `lab4/fix-readme-commit-example`.
- Branches always start from an up-to-date `main`. Changes are never committed directly to `main`.

## 2. Commit convention

Each commit represents one logical change.
Messages use a prefix such as docs, chore, feat, fix or test,
followed by an imperative description.
Related issue numbers are included for traceability.

```text
<prefix>: <imperative description> (#<issue>)
```

| Prefix | Use | Example from this repository |
| --- | --- | --- |
| `feat` | New application behaviour | `feat: add health endpoint (#132)` |
| `test` | Automated tests | `test: add health endpoint test and local run instructions (#132)` |
| `docs` | Documentation only | `docs: align README commit example with convention (#162)` |
| `chore` | Maintenance and configuration | `chore: add Python gitignore` |
| `fix` | Correction of a defect | — |

Files are staged explicitly (`git add <file> ...`, not `git add .`) and the staged content is checked with `git diff --staged` before committing.

## 3. Workflow from issue to release

1. **Issue.** Move the issue to *In Progress* on the project board.
2. **Branch.** Create the branch from the issue and switch to it:
   `git fetch origin` and `git switch <branch>`.
3. **Update.** If `main` has moved, merge it into the branch with `git merge origin/main`. Pushed commits are not rebased.
4. **Commit.** Make at least two logical commits, each referencing the issue.
5. **Interrupt (when needed).** Shelve unfinished work with `git stash push -u -m "WIP: ..."`, fix the unrelated problem on its own branch through a pull request, return to the task branch and run `git stash pop`.
6. **Test.** Run the automated tests (`python -m pytest -v`) and check the issue's *Done when* conditions.
7. **Push.** `git push -u origin <branch>`.
8. **Pull request.** Open it into `main` with `Closes #<issue>` in the description (`Refs #<issue>` for partial work) and move the issue to *In Review*.
9. **Review and merge.** Review the diff, leave a review comment and merge with a merge commit.
10. **Check.** Confirm that the issue closed itself and that the card moved to *Done*.
11. **Sync.** `git switch main`, `git pull`, `git branch -d <branch>`, `git fetch --prune`, and delete the merged remote branch.
12. **Release.** Create an annotated tag, push it explicitly and publish the GitHub Release.

### Applied to #132

| Step | Evidence |
| --- | --- |
| 1. Issue | Reported: #132 was moved to *In Progress*. |
| 2. Branch | Verified: `132-t-22-1-fastapi-health-endpoint`, linked to #132 (`gh issue develop --list 132`). |
| 3. Update | Verified: the branch was 18 commits behind `main`; `main` was merged into it (`aebc07a`). |
| 4. Commit | Verified: `6353c7e` feat: add minimal FastAPI application structure (#132), `fb4118e` feat: add health endpoint (#132), `f90a70d` test: add health endpoint test and local run instructions (#132). |
| 5. Interrupt | Verified: with the health endpoint uncommitted (one modified file and two new files), the work was stashed with `git stash push -u -m "WIP: health endpoint (#132)"`. The README commit example was fixed on `lab4/fix-readme-commit-example` (`a80f2d6`, PR #164). `main` was merged back into the task branch (`e24f751`) and `git stash pop` restored the work without conflicts. |
| 6. Test | Verified: `pytest -v` passed (1 passed) and `GET /health` returned HTTP 200 with `{"status": "ok"}`. Reported: `python -m pytest -v` passed on Windows (1 passed). |
| 7–8. Push and PR | Verified: PR #165 into `main` with `Closes #132`. Reported: #132 was moved to *In Review*. |
| 9. Review and merge | Verified: self-review comment on #165; merged with merge commit `849318c`. |
| 10. Check | Verified: #132 was closed automatically by PR #165. Reported: the card was confirmed in *Done* on the board. |
| 11. Sync | Verified: local `main` matches `origin/main` at `849318c`. The merged branches were deleted: nine local branches with `git branch -d` and three remote branches (`132-t-22-1-fastapi-health-endpoint`, `lab4/fix-readme-commit-example`, `lab4/stash-practice`) with `git push origin --delete`, followed by `git fetch --prune`. Only `main` remains on the remote. |
| 12. Release | Verified: annotated tag `v0.1.0` on `849318c` and GitHub Release (see §6). |

## 4. Practices carried out

### Staging

git diff shows unstaged changes.
git diff --staged shows changes prepared for the next commit.
git restore --staged removes changes from staging without deleting the files.

Reported: after staging a file, it was edited again and both diffs were compared; `git restore --staged` was also practised.

### Merges

Verified:

- **Fast-forward:** `6b0bdba` (`lab4/fast-forward`) was merged without a merge commit, because the base branch had not moved; the history stays a straight line.
- **Merge commit:** `83508b3` joins `9d92711` and `fadf05d` (`lab4/merge-feature`), because both branches had advanced.

Details are recorded in docs/merge-practice.md.

### Conflict

Verified: `d73964d` (base branch) and `e8fffae` (`lab4/conflict-demo`) changed the same title line differently. The conflict was resolved manually by choosing a shared title, and the merge was completed in `3c57e25`.

### Stash

A plain `git stash push` leaves untracked files in the working directory; `git stash push -u` also shelves them. `git stash pop` restores the work and removes it from the list, while `git stash apply` restores it and keeps it.

- Verified: docs/stash-notes.md was added as the untracked file of the exercise; during the interruption a small fix was committed on `lab4/small-fix` (`e078dbc`) and merged in `3fc608c`. In Task 6, `git stash push -u` and `git stash pop` were used on #132 (§3).
- Reported: `git stash pop` and `-u` were practised; `git stash apply` restored the work while the stash stayed in the list, and the stash was then dropped.

### Collaboration between two copies

- Verified: two clones edited the same line of docs/remote-practice.md (`aac1216` and `ac079cf`), and the conflict was resolved in the merge commit `60dd1d0`, keeping both contributions.
- Reported: the push from copy B was rejected with `fetch first`. After `git fetch`, the branch was 1 commit ahead and 1 behind; `git pull --no-rebase` produced the conflict, which was resolved, and the push succeeded without force.

## 5. Main protection and pull-request review

Verified: `main` is protected by the repository ruleset **Protect main** (active on the default branch, with no bypass actors):

- a pull request is required before merging, with 0 required approvals;
- force pushes (non-fast-forward updates) are blocked;
- deletion of `main` is blocked.

This is an individual project, so there is no second reviewer. Each pull request is reviewed by its author: the full diff is checked and a comment records what was verified before merging. Verified: review comments on #163 and #165. Pull requests are merged with a merge commit to preserve the branch history.

## 6. Release

- Tags follow semantic versioning (`vMAJOR.MINOR.PATCH`). The first working version is `v0.1.0`.
- Verified: `v0.1.0` is an annotated tag on `849318c` (the merge of PR #165). Tags are not sent by `git push`, so the tag was pushed explicitly and is present on the remote.
- Release: <https://github.com/ceciliagalvaoo/hospital-devops/releases/tag/v0.1.0>
- Lightweight tag exercise. Reported: `v0.1.0-rc1` was created as a lightweight tag, pushed, then deleted locally (`git tag -d v0.1.0-rc1`) and on the remote (`git push origin --delete v0.1.0-rc1`). Verified: only `v0.1.0` remains on the remote.

## 7. History

The repository history was saved in docs/git-history.txt with:

```bash
git log --oneline --graph --decorate --all
```

It was captured after the `v0.1.0` tag was created and before the merged branches were cleaned up, so it still shows those branches.

## 8. Completion

- Verified: the merged local and remote branches were deleted (§3, step 11).
- This documentation is merged into `main` through a pull request referencing #162.
