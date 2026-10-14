---
name: Task
about: An implementation, testing or documentation task within a user story.
title: "T-XX.Y — <short task description>"
labels: ["task"]
assignees: []
---

<!--
Prefix test tasks with [TEST][auto] or [TEST][manual] after the identifier,
for example "T-XX.Y — [TEST][auto] <short description>".
Add this issue as a sub-issue of its user story (Relationships → Add parent), never directly under an epic.
Set the Project fields: Epic, Item type = task and the story's Sprint. Leave Story points empty.
-->

## Description
<The concrete objective of this task.>

## Parent user story
#N (US-XX — <story name>)

## Done when
- [ ] <Verifiable completion condition.>
- [ ] <Verifiable completion condition.>
- [ ] The change is merged into main through a pull request that references this issue.

## Classification
<One of: Implementation | Formal code test — automated | General test case — manual | Documentation>

## Dependencies
Blocked by:
- #N (T-XX.Y — <task description>)

<!-- Also register each dependency natively: Relationships → Mark as blocked by. Write "None." if there are none. -->
