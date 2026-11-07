# Docker build

This document describes how the application image is built, run and tagged. It is the reference for the manual build (Lab 6, Task 8) and for the automated pipeline that publishes the image (US-24). The report for Lab 6, Tasks 0–7, is in [docker-build-lab.md](docker-build-lab.md).

## Commands

All commands run from the repository root.

**Build** the image. The build arguments are optional and only set the image labels:

```bash
docker build \
  --build-arg APP_VERSION=0.1.0 \
  --build-arg VCS_REF="$(git rev-parse --short HEAD)" \
  -t hospital-devops:0.1.0 .
```

**Run** the complete stack (application, PostgreSQL and migrations) with Docker Compose, using settings from `.env`:

```bash
docker compose up --build
```

Run only the application container. Without a database, `GET /health` reports HTTP 503:

```bash
docker run --rm -p 8000:8000 hospital-devops:0.1.0
```

**Tag** the same image with further names locally. All tags point to the same image ID. Published images are tagged by CI (see [Versioning and image tags](#versioning-and-image-tags)):

```bash
docker tag hospital-devops:0.1.0 hospital-devops:0.1
docker tag hospital-devops:0.1.0 hospital-devops:sha-"$(git rev-parse --short HEAD)"
docker tag hospital-devops:0.1.0 ghcr.io/ceciliagalvaoo/hospital-devops:0.1.0
docker images hospital-devops
```

**Inspect** the result:

```bash
docker images hospital-devops                                                   # size
docker history hospital-devops:0.1.0                                            # layers
docker image inspect hospital-devops:0.1.0 --format '{{json .Config.Labels}}'   # labels
docker image inspect hospital-devops:0.1.0 --format '{{.Config.User}}'          # runtime user
```

Build only the first stage, for example to debug the dependency installation:

```bash
docker build --target build -t hospital-devops:build .
```

## Versioning and image tags

Published images are built and pushed by the `Publish` job of the CI workflow (`.github/workflows/ci.yml`) to `ghcr.io/ceciliagalvaoo/hospital-devops`. The job runs only after `Lint`, `Tests`, `E2E` and `Container` passed on the same commit, and `scripts/image_metadata.py` computes the version and the tags:

| Event | Image tags | `org.opencontainers.image.version` |
| --- | --- | --- |
| Push to `main` (a merged pull request) | `main`, `sha-<commit>` | `git describe` of the commit, for example `0.1.0-97-g437b1b4`: 97 commits after release `v0.1.0`, at commit `437b1b4` |
| Push of a release tag `vX.Y.Z` | `X.Y.Z`, `X.Y`, `latest`, `sha-<commit>` | `X.Y.Z` |

`<commit>` is the first seven characters of the commit SHA, and `org.opencontainers.image.revision` always holds the full SHA, so every published image can be traced to its source commit.

- **Immutable tags:** `sha-<commit>` and `X.Y.Z` always refer to the same image. A release tag is never moved (`docs/branching-strategy.md` §4), so `X.Y.Z` is published once.
- **Moving tags:** `main` follows the latest merged commit; `X.Y` follows the latest patch release of a minor version; `latest` follows the latest release, never an unreleased commit of `main`.
- **Releases** follow semantic versioning (`docs/branching-strategy.md` §4); there is one release per sprint (`v0.2.0` at the end of Sprint 1). A release tag must have the form `vMAJOR.MINOR.PATCH` and point to a commit on `main`; otherwise the `Publish` job fails and nothing is published. The `Tag and push` step pushes the tags one after the other, so a failure part-way leaves the earlier tags published.
- **Pull requests and manual runs** never publish; the `Publish` job is skipped for them, and it is the only job with permission to write packages.
- **Verification:** after each publication, the `Verify image` job pulls the `sha-<commit>` tag anonymously, starts it with PostgreSQL and checks `/health`, the login page, the non-root user and the `source`, `revision` and `version` labels (`pytest -m published`, README §11).

To run a specific build, use its immutable tag or its digest, which the run summary of the `Publish` job records:

```bash
docker pull ghcr.io/ceciliagalvaoo/hospital-devops:sha-437b1b4
docker image inspect ghcr.io/ceciliagalvaoo/hospital-devops:sha-437b1b4 \
  --format '{{index .Config.Labels "org.opencontainers.image.version"}} {{index .Config.Labels "org.opencontainers.image.revision"}}'
```

The package is public and linked to this repository through the `org.opencontainers.image.source` label: <https://github.com/ceciliagalvaoo/hospital-devops/pkgs/container/hospital-devops>.

## Dockerfile structure

The `Dockerfile` is a multi-stage build with two stages.

| Stage | Base | Purpose |
| --- | --- | --- |
| `build` | `python:3.13.18-slim` | Creates the virtual environment `/opt/venv` without its own pip and installs the runtime dependencies from `requirements.txt` into it with the base image's pip. A BuildKit cache mount keeps the pip download cache between builds without adding it to a layer. |
| `runtime` | `python:3.13.18-slim` | Creates the unprivileged user `app` (UID 10001), copies `/opt/venv` from the `build` stage and the application files (`alembic.ini`, `migrations/`, `app/`), and starts Uvicorn as UID 10001 in exec form. |

Only the `runtime` stage becomes the image. The `build` stage, the pip cache and `requirements.txt` are not part of it.

Order of the instructions and its effect on the layer cache:

1. `requirements.txt` is copied and installed before any application code, so editing a `.py` file reuses the dependency layers.
2. The application files are copied last, in the order of how often they change: `alembic.ini`, `migrations/`, `app/`.
3. `ARG APP_VERSION`, `ARG VCS_REF` and the `LABEL` instruction come after every layer with files. A new version or commit changes only the image metadata, so every cached layer is reused.

The `.dockerignore` is an allowlist: it excludes everything and includes only `app/`, `migrations/`, `alembic.ini` and `requirements.txt`. Tests, documentation, `.env`, `.git` and any new file in the repository stay out of the build context by default.

## Image labels

| Label | Value |
| --- | --- |
| `org.opencontainers.image.title` | `hospital-devops` |
| `org.opencontainers.image.description` | Hospital management web application (FastAPI and PostgreSQL) |
| `org.opencontainers.image.source` | `https://github.com/ceciliagalvaoo/hospital-devops` |
| `org.opencontainers.image.version` | Build argument `APP_VERSION` (default `0.0.0`) |
| `org.opencontainers.image.revision` | Build argument `VCS_REF` (default `unknown`) |

The `source` label links a package published to GitHub Container Registry to this repository. No `licenses` label is set, because the repository does not declare a license.

## Measurements

Measured on 2026-11-04 with Docker 28.5.1 on WSL 2 (linux/amd64). Times include BuildKit startup.

| Image | Size | Layers | Runs as | Contains pip in the application environment |
| --- | --- | --- | --- | --- |
| Single-stage Dockerfile (before) | 188 MB | 11 | UID 10001 | Yes |
| Multi-stage Dockerfile (current) | 188 MB | 10 | UID 10001 | No |

| Build | Time |
| --- | --- |
| Cold build, no cache | 20.2 s |
| Rebuild without changes | 1.1 s |
| Rebuild after editing `app/main.py` (only `COPY app` is rebuilt) | 1.2 s |
| Rebuild with a new `APP_VERSION` and `VCS_REF` (all layers cached) | 1.1 s |
| Rebuild after changing `requirements.txt`, with a warm pip cache mount | 11.9 s |

The build context shrank from 19.34 kB with the previous denylist `.dockerignore` to 937 B with the allowlist.

The multi-stage build does not reduce the size here, unlike in the .NET and Java examples of Lab 6. Python has no separate compiler or SDK: the runtime dependencies are the same in both versions (69.4 MB), and both start from the same slim base image. The gains are elsewhere: the application environment has no pip, the build tooling and caches stay in the discarded stage, and the stages separate dependency installation from the runtime configuration. A first version that created the virtual environment with its own pip produced a 198 MB image, so the virtual environment is created with `--without-pip`.

## Choice of base image

The base image is `python:3.13.18-slim`, pinned to the patch version in the `ARG PYTHON_IMAGE` line of the Dockerfile.

- **Python 3.13** matches the version used by CI (`PYTHON_VERSION` in `.github/workflows/ci.yml`); a CI smoke test fails if the two differ.
- **`slim`** is the Debian variant without compilers and documentation. Every dependency is available as a prebuilt wheel (including `psycopg[binary]` and `bcrypt`), so no compiler is needed.
- **Not Alpine:** Alpine uses musl instead of glibc, so many prebuilt wheels do not apply and packages must be compiled, which makes builds slower and less predictable.
- **Not distroless:** the smoke tests and the Compose commands run `sh`, `id` and `alembic` inside the container, which a distroless image does not provide.

The digest of the base image at the time of writing is:

```text
python@sha256:ae14d4ce8771606477a81446e7ef429edd6762305fc50c84507c1041fa8285d1
```

To update the base image, change the tag in `ARG PYTHON_IMAGE`, keep `PYTHON_VERSION` in the CI workflow on the same minor version, rebuild, run `pytest -m smoke` and record the new digest here.
