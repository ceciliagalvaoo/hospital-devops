# US-23 manual checks

Manual test case of T-23.6 (#143): verify with a test pull request that failed required checks prevent merging into `main`. It checks the ruleset configured in #141 (`docs/branching-strategy.md` §3 and §7) from the point of view of the person who merges.

## Run

| | |
| --- | --- |
| Date | 2026-11-07 |
| Tester | Cecília Galvão |
| Ruleset | **Protect main** (id 25722097): pull request required, merge commits only, required checks `Lint`, `Tests`, `E2E` and `Container` with the branch up to date |
| `main` during the run | `ae010a0` |
| Test pull request | #209, `TEST — do not merge: failed checks block merging (#143)`, from the branch `143-test-blocked-merge` |
| Environment | GitHub web interface in Google Chrome 156.0.8078.80 on Windows 11 Pro (build 26200), signed in as the repository owner (administrator); merge state confirmed with the GitHub GraphQL API (`mergeStateStatus`, `isRequired`, `viewerCanMergeAsAdmin`) |

Result values: **Pass**, or **Fail** with a link to the defect issue.

## Procedure

1. The branch `143-test-blocked-merge` was created from `abea11d`, one merge commit behind `main`, so that it was out of date.
2. Commit `835634d` added `tests/test_blocked_merge_demo.py`, with a failing test and an unused import (Ruff F401). Pull request #209 was opened with `Refs #143`, not `Closes`.
3. Commit `e1025bd` removed the file again.
4. **Update branch** merged `main` into the branch (`85d6474`).
5. The pull request was closed without merging and the branch was deleted.

| Head commit | CI run | Result |
| --- | --- | --- |
| `835634d` (failure added) | 42391283206 | `Lint` and `Tests` failed; `E2E` and `Container` passed |
| `e1025bd` (failure removed) | 42391560459 | all four passed |
| `85d6474` (after **Update branch**) | 42391842249 | all four passed |

## Checks

| ID | Check | Expected result | Observed | Result |
| --- | --- | --- | --- | --- |
| M1 | Checks still running | The merge is blocked while the required checks have not completed. | After pushing `e1025bd`, the four checks were *Queued*, each marked *Required*, and **Merge pull request** was disabled ([evidence](us-23-evidence/m1-checks-running.png)). | Pass |
| M2 | Failed `Tests` check | The merge is blocked and the failed check is marked as required. | `Tests` failed and was marked *Required*; **Merge pull request** was disabled. The API reported `Tests=FAILURE required=true` ([evidence](us-23-evidence/m2-m4-failed-checks.png)). | Pass |
| M3 | Failed `Lint` check | The merge is blocked and the failed check is marked as required. | `Lint` failed and was marked *Required*; the merge stayed disabled. The API reported `Lint=FAILURE required=true` (same evidence as M2). | Pass |
| M4 | No bypass, one merge method | No option merges despite the failures, and only a merge commit is offered. | The merge box offered no option to bypass the requirements, and the API reported `viewerCanMergeAsAdmin=false` for the repository administrator (same evidence as M2). When the button was enabled in M6, it had no menu of other merge methods. | Pass |
| M5 | Passing checks on an outdated branch | The merge stays blocked while the branch is behind `main`, and **Update branch** is offered. | With all four checks passed on `e1025bd`, the merge stayed disabled with "This branch is out-of-date with the base branch" and **Update branch**. The API reported `mergeStateStatus=BEHIND` ([evidence](us-23-evidence/m5-passed-but-behind.png)). | Pass |
| M6 | Up-to-date branch with passing checks | The merge becomes possible. | After **Update branch** and four passed checks on `85d6474`, **Merge pull request** was enabled ([evidence](us-23-evidence/m6-mergeable.png)). The pull request was then closed without merging (`mergedAt` empty) and `main` stayed at `ae010a0`. | Pass |

## Summary

6 of 6 checks pass. A failed or unfinished required check, and a branch behind `main`, each block the merge, even for the repository administrator; the merge is possible only with all four checks passed on an up-to-date branch, and only as a merge commit. No defect was found. The test pull request #209 was closed without merging and its branch was deleted.
