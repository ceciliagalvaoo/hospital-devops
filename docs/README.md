# Documentation

Index of the project documentation. The [README](../README.md) has the project overview and a quickstart.

## Product

- [Requirements](requirements.md): functional and non-functional requirements, user roles, the RBAC matrix and how access is enforced.
- [Product backlog](backlog.md): the ordered user stories, prioritisation, acceptance criteria and the Definition of Done.
- [Task decomposition](tasks.md): the tasks of every story, by epic.
- [Story-point estimation](estimation.md): scale, reference story, estimates and velocity.

## Process

- [Sprint planning](planning.md): sprint duration, ceremonies, backlog refinement and the projected sprint backlogs.
- [Project management on GitHub](github-project.md): the GitHub Project, labels, fields, status workflow and WIP limits, views, automation, branch names and dependencies.
- Sprint records: [Sprint 1](sprints/sprint-1.md), [Sprint 2](sprints/sprint-2.md).
- [Test plan](testing.md): the tests of every user story, the test types, the pipeline, the thresholds and a failed and fixed run.
- Test records: [US-01 automated tests](testing/us-01-automated-tests.md), [US-01 manual checks](testing/us-01-manual-checks.md), [US-02 automated tests](testing/us-02-automated-tests.md), [US-02 manual checks](testing/us-02-manual-checks.md), [US-03 automated tests](testing/us-03-automated-tests.md), [US-03 manual checks](testing/us-03-manual-checks.md), [US-09 automated tests](testing/us-09-automated-tests.md), [US-10 automated tests](testing/us-10-automated-tests.md), [US-13 automated tests](testing/us-13-automated-tests.md), [US-14 automated tests](testing/us-14-automated-tests.md), [US-23 manual checks](testing/us-23-manual-checks.md), [US-24 manual checks](testing/us-24-manual-checks.md).

## Architecture

- [Architecture](architecture.md): components, data model, request flow, delivery and tests, as implemented.
- [Tools and technology stack](tooling.md): the tools chosen and the planned architecture and scope.
- [Diagrams](diagrams/): draw.io sources and PNG exports ([activity: appointment](diagrams/activity-appointment.png), [branching strategy](diagrams/branching-strategy.png)).

## Development

- [Running locally](development/running-locally.md): install, run, containers, Docker Compose, development accounts and the pages.
- [Testing and code quality](development/testing.md): unit, integration, smoke, end-to-end and published-image tests, Ruff and the coverage gate.
- [Continuous integration](development/ci.md): the CI jobs, required checks and deliberate failures.
- [Database migrations](development/migrations.md): Alembic commands and conventions.
- [Accounts, sessions and access control](development/authentication.md): staff accounts, login endpoints, sessions, route protection and CSRF.
- [Branching strategy](development/branching-strategy.md): branches, pull requests, releases and tags.
- [Git workflow](development/git-workflow.md): the workflow from issue to release, as practised.

## Delivery

- [Container image](docker-build.md): the Dockerfile, build arguments and image tags.
- [Versioning](versioning.md): scheme, channels, tag format and who may release.
- [Publishing](publishing.md): registry, pipeline stages, credentials, consumption, revocation and withdrawal.

## Labs

- Lab 4 and Lab 5 Git practice: [Git tips](labs/git-tips.md), [merge practice](labs/merge-practice.md), [remote practice](labs/remote-practice.md), [stash notes](labs/stash-notes.md), [history](labs/git-history.txt).
- Lab 6: [Docker build report](docker-build-lab.md).
- Lab 7: [testing report](testing-lab.md) ([evidence](lab7-evidence/)).
- Lab 8: [publishing report](publishing-lab.md) ([evidence](lab8-evidence/)).
