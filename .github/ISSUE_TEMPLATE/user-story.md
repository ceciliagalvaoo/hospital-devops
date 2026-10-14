---
name: User story
about: A user story with acceptance criteria, Definition of Done and an estimate.
title: "US-XX — <short story name>"
labels: ["user-story"]
assignees: []
---

<!--
Add this issue as a sub-issue of its epic (Relationships → Add parent).
Create at least one [TEST][auto] or [TEST][manual] task as a sub-issue of this story.
Set the Project fields: Story points, Priority, Sprint, Epic and Item type = story.
-->

## Story
As a <role>, I want <capability>, so that <benefit>.

## Acceptance criteria
- [ ] Given <context>, when <action>, then <expected result>.
- [ ] Given <context>, when <action>, then <expected result>.

## Definition of Done
- [ ] Its acceptance criteria are satisfied.
- [ ] Changes are merged into main through a pull request, never pushed directly.
- [ ] Relevant unit tests are written and pass in CI.
- [ ] The end-to-end test for the affected workflow passes.
- [ ] Manual test cases, where defined, are executed and documented.
- [ ] Authorisation tests verify relevant allowed and denied access.
- [ ] The container image builds successfully and is published to GitHub Container Registry (GHCR).
- [ ] The README is updated if a requirement or design decision changes.

## Dependencies
Blocked by:
- #N (US-XX — <story name>)

<!-- Also register each dependency natively: Relationships → Mark as blocked by. Write "None." if there are none. -->

## Story Points
<1, 2, 3, 5 or 8 — split the story if it is 13>

## Planned sprint
<Sprint N, or "Optional backlog — not planned in any sprint">
