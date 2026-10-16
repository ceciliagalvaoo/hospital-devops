---
name: Defect
about: A defect found during automated or manual testing.
title: "T-XX.Y — [DEFECT] <short description of the failure>"
labels: ["task", "defect"]
assignees: []
---

<!--
Use the identifier of the next free task in the affected story (T-XX.Y), so the defect stays traceable.
Add this issue as a sub-issue of the affected user story (Relationships → Add parent), never directly under an epic.
Set the Project fields: Epic and Sprint of the affected story, Item type = defect, Status = Backlog. Leave Story points empty.
If the defect blocks other work, register it natively: Relationships → Mark as blocking.
-->

## Description
<What fails, in one or two sentences.>

## Affected user story
#N (US-XX — <story name>)

## Found by
#N (T-XX.Y — <test task>), or <manual check / review / other>

## Steps to reproduce
1. <Step>
2. <Step>

## Expected result
<What should happen, according to the acceptance criteria.>

## Actual result
<What happens instead, including error messages or HTTP status codes.>

## Environment
<Branch or commit SHA, container image tag, browser, test data used. Never include real patient information.>

## Done when
- [ ] The failure no longer occurs when following the steps to reproduce.
- [ ] An automated test that reproduces the defect is added and passes.
- [ ] The fix is merged into main through a pull request that references this issue.

## Classification
Defect

## Dependencies
Blocked by:
- None.
