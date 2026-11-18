# Versioning

This document defines how the artifact of `hospital-devops` is versioned (Lab 8, Task 5, #227). The artifact is the application's container image, `ghcr.io/ceciliagalvaoo/hospital-devops`; how it is built, published and consumed is described in [docker-build.md](docker-build.md) and how it is published, consumed and withdrawn in [publishing.md](publishing.md).

## 1. Scheme

The project uses [Semantic Versioning](https://semver.org): `MAJOR.MINOR.PATCH`, with an optional pre-release (`-rc.N`, `-dev.N`).

| Change | Increase | Examples in this project |
| --- | --- | --- |
| Incompatible change that users or integrations rely on | **MAJOR** | a removed or renamed URL or JSON field, a configuration variable that must change, a migration that needs manual steps |
| New functionality that stays compatible | **MINOR** | the user stories delivered by a sprint; there is one minor release per sprint (`v0.2.0` for Sprint 1, `v0.3.0` for Sprint 2) |
| Compatible bug fixes only | **PATCH** | defect fixes released between two sprints, such as `v0.2.1` |

While the version is `0.y.z`, the application is in initial development and may still change; `1.0.0` is reserved for the first version considered stable for its intended use (`docs/development/branching-strategy.md` §4).

Pre-releases sort **before** their release, and their numeric parts compare as numbers: `0.3.0-dev.2` < `0.3.0-dev.10` < `0.3.0-rc.1` < `0.3.0` < `0.3.1`.

## 2. Channels

| Channel | Created by | Version | Who uses it | Kept |
| --- | --- | --- | --- | --- |
| **dev** | every push to `main` that passes the required checks | `X.Y.Z-dev.N`: the next version after the latest tag, numbered by the CI run, for example `0.3.0-dev.57` | development, the Sprint Review demonstration | short: see the clean-up policy in [publishing.md](publishing.md) §8 |
| **rc** | a tag `vX.Y.Z-rc.N` | `X.Y.Z-rc.N`, for example `0.2.1-rc.1` | acceptance testing before a release | until the release |
| **release** | a tag `vX.Y.Z` | `X.Y.Z` | everyone who runs the application | forever |

Pull requests have no channel: they are built and tested, never published.

The next dev version follows the latest version tag in the history of the commit: after `v0.2.0` or `v0.2.1`, `main` builds are `0.3.0-dev.N`; after a release candidate `v0.3.0-rc.1`, they stay `0.3.0-dev.N`, because `0.3.0` is not released yet; after `v0.3.0`, they become `0.4.0-dev.N`.

## 3. Tag format

- Only two forms of git tag create a version: `vMAJOR.MINOR.PATCH` (release) and `vMAJOR.MINOR.PATCH-rc.N` with `N` ≥ 1 (release candidate). Numbers have no leading zeros.
- Any other tag on a pushed commit, for example `v0.2`, `v0.2.0-rc1` or `v0.2.0-beta.1`, makes the publication fail, so a mistyped tag can never publish an image.
- Release tags are **annotated** tags on a commit of `main` that passed the pipeline.
- The version is never typed into a workflow: `scripts/image_metadata.py` derives it from the git reference, the tags in the history and the CI run number, and its unit tests (`tests/test_image_metadata.py`) cover every case above.

## 4. Mutable and immutable names

| Name | Example | Moves? | Use |
| --- | --- | --- | --- |
| Commit tag | `sha-5021ac3` | **never** | identifies the tested build of one commit |
| Exact version | `0.3.0-dev.57`, `0.2.1-rc.1`, `0.2.1` | **never** | the thing to deploy and reproduce |
| Digest | `hospital-devops@sha256:…` | **never** | exact reproducibility; what a deployment manifest should name |
| Channel tag | `dev`, `rc` | yes | the newest build of a channel |
| Floating release tags | `0.2`, `latest` | yes | the newest patch of a minor line, the newest release |

Deployments name an exact version or a digest, never a moving tag: `latest` says nothing about what is running and changes when a release is published.

The image of a commit is built once; the channel names are added to it without a rebuild, so all names of one commit share one digest ([docker-build.md](docker-build.md#versioning-and-image-tags)). A promoted image keeps the version label of its dev build, because the label is part of the tested bytes.

## 5. Who may create a release

- Only the project owner creates and pushes `v*` tags (`docs/development/branching-strategy.md` §4) and approves releases.
- Release tags are never moved, deleted or re-created: a correction is released as a new version.
- A version that is published once is never published again with different content; the registry name of an exact version is therefore safe to deploy. Defect #224 recorded the one violation, the `v0.2.0` release run re-pushing `sha-b155343`; since #228 a release only adds names and never pushes the commit tag.
