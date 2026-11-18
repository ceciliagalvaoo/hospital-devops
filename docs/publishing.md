# Publishing

This document describes how the artifact of `hospital-devops` is published, consumed and withdrawn (Lab 8, Task 5, #229). The version rules are in [versioning.md](versioning.md); how the image is built and named is in [docker-build.md](docker-build.md#versioning-and-image-tags).

## 1. Artifact and registry

| Item | Value |
| --- | --- |
| Artifact | the application's container image, which runs both the web application and its database migrations |
| Registry | GitHub Container Registry (GHCR) |
| Name | `ghcr.io/ceciliagalvaoo/hospital-devops` |
| Visibility | public: anyone can pull it without credentials |
| Package page | <https://github.com/ceciliagalvaoo/hospital-devops/pkgs/container/hospital-devops> |

**Why a container image.** The application is a web service with a PostgreSQL database, not a library: nobody installs it with `pip`. What runs in every environment is the image, with its Python version, dependencies and non-root user fixed at build time, so the image is the thing to version, test and promote.

**Why GHCR.**
- The code, the pipeline and the packages live in one place, and the package is linked to the repository through the `org.opencontainers.image.source` label.
- The pipeline publishes with the workflow's own `GITHUB_TOKEN`; no long-lived secret has to be created or stored.
- Public images are free to store and to pull, without the anonymous pull limits of Docker Hub.
- Docker Hub would add a second account and a stored access token; a cloud registry (ECR, Artifact Registry) would add a cloud account and its credentials. Neither is needed while the project has no cloud deployment.

## 2. Channels and names

| Channel | Created by | Names | Who uses it |
| --- | --- | --- | --- |
| dev | every push to `main` that passed the required checks | `sha-<commit>`, `X.Y.Z-dev.N`, `dev` | development, the Sprint Review demonstration |
| rc | a tag `vX.Y.Z-rc.N` | `X.Y.Z-rc.N`, `rc` | acceptance testing before a release |
| release | a tag `vX.Y.Z`, after approval | `X.Y.Z`, `X.Y`, `latest` | everyone who runs the application |

The rc and release names are added to the image that the dev channel already published for the tagged commit, so all names of one commit have **one digest**. `sha-<commit>`, `build-<commit>` and the exact versions never move; `dev`, `rc`, `X.Y` and `latest` move ([versioning.md](versioning.md) §4). The tag `main` is no longer updated since #228; `dev` replaces it.

## 3. Pipeline stages

| Stage | Workflow and job | What it does | Writes to the registry |
| --- | --- | --- | --- |
| 1. Check | CI: `Lint`, `Tests`, `E2E` | static checks, unit and integration tests with 100% coverage, browser tests | no |
| 2. Build and test | CI: `Container` | builds the image **once** with its version and commit labels and runs the smoke tests against it; on `main`, hands it to `Publish` as an artifact | no |
| 3. Publish (dev) | CI: `Publish`, environment `test` | on `main` only, after stages 1 and 2 passed: pushes the tested image and names it `sha-<commit>`, `X.Y.Z-dev.N`, `dev`; checks the digests | yes |
| 4. Verify | CI: `Verify image` | pulls `sha-<commit>` without credentials, starts it with PostgreSQL and checks health, login page, non-root user and labels | no |
| 5. Promote (rc) | Release: `Promote`, environment `test` | on a tag `vX.Y.Z-rc.N`: fails if the commit has no tested image, otherwise adds `X.Y.Z-rc.N` and `rc`; checks the digests | yes (names only) |
| 6. Promote (release) | Release: `Promote`, environment `production` | on a tag `vX.Y.Z`: **waits for the owner's approval**, then adds `X.Y.Z`, `X.Y` and `latest` | yes (names only) |
| 7. GitHub Release | Release: `GitHub Release` | creates the release with generated notes; a pre-release for rc | no (writes the repository) |

Pull requests run stages 1 and 2 only and never publish. The release workflow never builds and never pushes image content.

## 4. Credentials

| Credential | Used by | Where it is stored | Scope and lifetime |
| --- | --- | --- | --- |
| `GITHUB_TOKEN` | `Publish` (CI) and `Promote` (Release), to log in to GHCR | created by GitHub Actions for each run; never stored in the repository or in a secret | `packages: write` in those two jobs only, `contents: write` in `GitHub Release` only, `contents: read` everywhere else; expires when the job ends |
| none | consumers pulling the image | — | the package is public |
| the owner's GitHub account | approving the `production` environment, pushing tags | GitHub sign-in | the only required reviewer of `production`; `production` accepts deployments from `v*` tags only |

No personal access token, password or registry secret is used by the pipeline, and none is stored in the repository, in `.env` files or in repository secrets. If a maintainer ever needs to push to GHCR from a computer, they use a **classic personal access token with only `write:packages`** and a short expiry (GHCR does not accept fine-grained tokens), log in with `docker login ghcr.io --password-stdin`, and keep it in the Docker credential store, never in a file of the repository.

## 5. Consuming the image

Use an **exact version or a digest** in anything that is deployed; the moving names are for trying things out.

```bash
# Release (what to deploy)
docker pull ghcr.io/ceciliagalvaoo/hospital-devops:0.2.1
docker pull ghcr.io/ceciliagalvaoo/hospital-devops@sha256:27fa0ed2f1ed09d72f310c255319abf529bea06d4478970ba89be1225a9cfd16

# Release candidate (acceptance testing)
docker pull ghcr.io/ceciliagalvaoo/hospital-devops:0.2.1-rc.1     # or :rc for the newest candidate

# Development build of one commit, or the newest one
docker pull ghcr.io/ceciliagalvaoo/hospital-devops:sha-f4bec54
docker pull ghcr.io/ceciliagalvaoo/hospital-devops:dev

# Which version and commit an image is
docker image inspect ghcr.io/ceciliagalvaoo/hospital-devops:0.2.1 \
  --format '{{index .Config.Labels "org.opencontainers.image.version"}} {{index .Config.Labels "org.opencontainers.image.revision"}}'
```

To run a published version with its database, from a clone of the repository with a `.env` copied from `.env.example` (README §11), name the image and start the stack without building:

```bash
export PUBLISHED_IMAGE=ghcr.io/ceciliagalvaoo/hospital-devops:0.2.1
export APP_ENV=production   # .env.example sets development, which also serves /docs
docker compose -f docker-compose.yml -f tests/published/compose.published-image.yml up -d --no-build --wait app
curl http://localhost:8000/health   # {"status":"ok","database":"ok"}
```

The `version` label of a promoted image is the version of its dev build (`0.3.0-dev.74` inside `0.2.1`): the label is part of the tested bytes, and changing it would need a rebuild. The registry name is the release version; the `revision` label is the commit that links both.

## 6. Revoking a leaked credential

1. **`GITHUB_TOKEN`** printed in a log: it already expired when its job ended. Delete the log of that run (*Actions* → the run → *Delete all logs*), and check the package's versions for names created outside the pipeline.
2. **A personal access token** with `write:packages`: revoke it at once in *GitHub* → *Settings* → *Developer settings* → *Personal access tokens* → *Delete*; run `docker logout ghcr.io` on every computer that used it; review the package's versions and the account's security log (*Settings* → *Security log*) for pushes made with it; create a new token only if it is still needed.
3. **The owner's account**: change the password, review the sessions and the two-factor settings, and check the `production` environment's reviewers and the ruleset of `main`.
4. In every case, a version pushed with the leaked credential is treated as faulty and withdrawn (§7), and the event is recorded in the sprint's work log.

## 7. Withdrawing a faulty release

A release tag and an exact version are never moved, deleted or re-published with other content ([versioning.md](versioning.md) §5). A faulty release is replaced, not rewritten:

1. **Mark it.** Edit its GitHub Release: start the notes with "Withdrawn: <reason>. Use vX.Y.Z+1." so nobody picks it from the releases page.
2. **Point the moving names back** to the previous good release, so that `latest` and `X.Y` stop serving it (with a token that has `write:packages`, §4):
   ```bash
   docker buildx imagetools create \
     --tag ghcr.io/ceciliagalvaoo/hospital-devops:latest \
     --tag ghcr.io/ceciliagalvaoo/hospital-devops:0.2 \
     ghcr.io/ceciliagalvaoo/hospital-devops:0.2.0
   ```
3. **Release the fix** as a new PATCH version through the normal flow (pull request, `vX.Y.Z+1-rc.1`, `vX.Y.Z+1`); its promotion moves `latest` and `X.Y` forward again.
4. **Delete the image version** from the package page only when keeping it is dangerous (a leaked secret inside the image, a security flaw that is being exploited): deleting breaks everyone who pinned it, so it is a last resort, and it is recorded in the release notes and the work log.

## 8. Clean-up of old images

GHCR keeps every version until it is deleted. The policy:

- Versions with a release or rc name are kept.
- Dev versions (`sha-<commit>`, `build-<commit>`, `X.Y.Z-dev.N`) older than 30 days and without a release or rc name may be deleted from the package page at the end of a sprint.
- The stale tag `main` (last updated before #228) may be deleted in the first clean-up.

On 2026-11-18 the package holds 39 versions; no clean-up has been needed yet.

## 9. Evidence: the first promoted release

`v0.2.1` is a PATCH release with the fixes #222, #224 and #225. (`v0.1.0` and `v0.2.0` already existed and are immutable, so the lab's `v0.1.0-rc.1` → `v0.1.0` example was applied to the next version.)

| Step | Run | Result |
| --- | --- | --- |
| Merge of #228 into `main` (f4bec54) | CI 44289049451 | all six jobs passed; published `sha-f4bec54`, `0.3.0-dev.74`, `dev` |
| Tag `v0.2.1-rc.1` on f4bec54 | Release 44290421084 | environment `test`; added `0.2.1-rc.1`, `rc`; pre-release created |
| Tag `v0.2.1` on f4bec54 | Release 44290895319 | environment `production`, approved by the owner; added `0.2.1`, `0.2`, `latest`; release created |

Digests read from the registry after both releases:

| Name | Digest |
| --- | --- |
| `sha-f4bec54` (tested image) | `sha256:27fa0ed2f1ed09d72f310c255319abf529bea06d4478970ba89be1225a9cfd16` |
| `0.3.0-dev.74` | the same |
| `0.2.1-rc.1`, `rc` | the same |
| `0.2.1`, `0.2`, `latest` | the same |
| `0.2.0` (previous release) | `sha256:e92b7c304dddab8e42d66b0f1e7cf9a38cc268ceff0bea0cc32f5b2f7d0a9687`, unchanged |

`sha-f4bec54` had the same digest before and after the release runs, so the releases did not re-push the commit tag (#224). The release notes of both versions were generated from the merged pull requests #226, #231, #232, #233 and #234. Started from the registry with the commands of §5, `0.2.1` answered `/health` with `{"status":"ok","database":"ok"}`, the login page with HTTP 200 and `/docs` with HTTP 404.
