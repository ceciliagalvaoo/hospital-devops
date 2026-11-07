# US-24 manual checks

Manual test case of T-24.4 (#149): pull requests cannot publish release images, and the published SHA matches its source commit. It checks the `Publish` and `Verify image` jobs (#146, #147, #148) and the versioning scheme in [docs/docker-build.md](../docker-build.md#versioning-and-image-tags).

## Run

| | |
| --- | --- |
| Date | 2026-11-07 |
| Testers | Cecília Galvão (P1, P6, in the GitHub interface); Claude Code on her machine (P2–P5, command line), reviewed by Cecília Galvão |
| Image | `ghcr.io/ceciliagalvaoo/hospital-devops` |
| `main` during the run | `4fcbce3` (merge of #213), published by run 42396037360 |
| Pull requests checked | #211, #212, #213 |
| Environment | GitHub web interface in Google Chrome 156.0.8078.80 on Windows 11 Pro (build 26200); command line in WSL 2, Ubuntu 24.04.3 LTS, with Docker 28.5.1, Docker Compose 2.40.2, GitHub CLI 2.102.0 and Git 2.43.0. Registry requests and pulls were made **without credentials** (`docker logout ghcr.io`, anonymous registry token). |

Result values: **Pass**, or **Fail** with a link to the defect issue.

## Checks

| ID | Check | Steps | Expected result | Observed | Result |
| --- | --- | --- | --- | --- | --- |
| P1 | Pull requests skip publication | Open the checks of a pull request after `Publish` and `Verify image` exist; read the jobs of the CI runs of #211, #212 and #213 (`gh run view <run> --json jobs`). | `Publish` and `Verify image` are skipped; only the four required checks run. | The checks of #211 show `CI / Publish (pull_request)` as *Skipped* and not required ([evidence](us-24-evidence/p1-pull-request-publish-skipped.png)). Runs 42393050817 (#211), 42394413722 (#212) and 42395724647 (#213): `Publish=skipped`; `Verify image=skipped` in #213, the first run that had the job. | Pass |
| P2 | No image for pull-request commits | List the registry tags anonymously (`GET /v2/ceciliagalvaoo/hospital-devops/tags/list`) and request the manifest `sha-<head>` of each pull request's head commit. | No tag exists for a pull-request head commit. | Tags: `main`, `sha-6b0482d`, `sha-4fcbce3`, all merge commits on `main`. The manifests `sha-ba92374` (#211), `sha-7c4dbfb` (#212) and `sha-78bbde3` (#213) return HTTP 404. | Pass |
| P3 | Manual runs do not publish | Start the workflow manually on `main` (`gh workflow run CI --ref main`), then list the registry tags again. | The checks run, `Publish` and `Verify image` are skipped, and no tag is added. | Run 42396448951: `Lint`, `Tests`, `E2E` and `Container` succeeded; `Publish` and `Verify image` skipped. The tag list was unchanged. | Pass |
| P4 | Published SHA matches the commit | Pull `sha-4fcbce3` and `main` anonymously; compare their digests and read the `revision` label; check that the commit is on `main` (`git merge-base --is-ancestor`). | Both tags have the same digest; `revision` is the full SHA of `4fcbce3`, which is on `main`. | Both digests are `sha256:30aab2d643950f55b096bac794bc881579f408ac455fdb9a3d68e76d3ca9a1b8`; `revision=4fcbce358ac6b22f0d690b763aa89c3a09eddb36`, the full SHA of `4fcbce3`, which is on `main`. | Pass |
| P5 | Image content matches the commit | Extract `app/`, `migrations/` and `alembic.ini` of `4fcbce3` with `git archive` and compare their SHA-256 hashes with the files in `/app` of the image; compare the versions installed in the image's environment (`/opt/venv`, read with `importlib.metadata`) with `requirements.txt` of the commit. | Every application file is identical; every pinned dependency is installed in the pinned version. | 29 of 29 application files are identical. All 8 pinned requirements of `4fcbce3` are installed in their pinned versions. `requirements.txt` itself is not copied into the runtime stage (`docs/docker-build.md`). | Pass |
| P6 | Package page | Open <https://github.com/ceciliagalvaoo/hospital-devops/pkgs/container/hospital-devops> without signing in. | The package is public, linked to this repository and lists `main` and the `sha-<commit>` tags. | Opened in a private Chrome window, without signing in: the package is marked *Public*, links to the repository `ceciliagalvaoo/hospital-devops` and lists the tagged versions `sha-4fcbce3` + `main` (same version) and `sha-6b0482d` ([evidence](us-24-evidence/p6-package-page.png)). The *Latest* badge is GitHub's label for the most recent version, not an image tag `latest`, which only release tags publish. *OS / Arch 2* lists the `linux/amd64` image and the build provenance attestation that BuildKit adds (`unknown/unknown`, checked in the image index). | Pass |

Notes on P5: the first comparison reported two differences that were caused by the check itself, not by the image: the file lists were sorted with different locales in WSL and in the container, and `pip freeze` returned nothing because the image's virtual environment has no pip. Sorting both lists with `LC_ALL=C` and reading the versions with `importlib.metadata` gave the results above.

## Summary

6 of 6 checks pass; no defect was found. Pull requests and manual runs skip `Publish` and `Verify image` and leave no image in the registry; only merges into `main` publish. The published image of `4fcbce3` is reachable by its `main` and `sha-4fcbce3` tags with one digest, carries the full commit SHA in its `revision` label, and contains exactly the application files and pinned dependencies of that commit. The package is public and linked to this repository.

The release tags (`X.Y.Z`, `X.Y`, `latest`) are checked with the first release, `v0.2.0`, in #186.
