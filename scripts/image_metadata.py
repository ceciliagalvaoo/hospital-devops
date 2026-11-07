"""Compute the version label and the tags of an image published by CI.

Used by the Publish job of .github/workflows/ci.yml; the scheme is documented in
docs/docker-build.md ("Versioning and image tags").

- A push to main publishes ``main`` and ``sha-<commit>``; the version is the ``git describe``
  of the commit, for example ``0.1.0-45-g437b1b4`` (45 commits after release v0.1.0).
- A release tag ``vX.Y.Z`` publishes ``X.Y.Z``, ``X.Y``, ``latest`` and ``sha-<commit>``
  with the version ``X.Y.Z``.

Any other ref is refused, so an unexpected trigger can never publish an image.
"""

import os
import re
import subprocess

MAIN_REF = "refs/heads/main"
RELEASE_TAG = re.compile(r"^refs/tags/v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
SHA = re.compile(r"^[0-9a-f]{40}$")


def image_metadata(ref: str, sha: str, describe: str) -> tuple[str, list[str]]:
    """Return the version and the image tags for a build of ``sha`` triggered by ``ref``."""
    if not SHA.match(sha):
        raise ValueError(f"Expected a full 40-character commit SHA, got {sha!r}.")
    commit_tag = f"sha-{sha[:7]}"
    release = RELEASE_TAG.match(ref)
    if release:
        major, minor, patch = release.groups()
        version = f"{major}.{minor}.{patch}"
        return version, [version, f"{major}.{minor}", "latest", commit_tag]
    if ref == MAIN_REF:
        return describe.removeprefix("v"), ["main", commit_tag]
    raise ValueError(
        f"Images are published only from {MAIN_REF} or release tags vMAJOR.MINOR.PATCH, "
        f"not from {ref!r}."
    )


def main() -> None:  # pragma: no cover - runs in the CI job
    describe = subprocess.run(
        ["git", "describe", "--tags", "--match", "v[0-9]*", "--always"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    version, tags = image_metadata(os.environ["GITHUB_REF"], os.environ["GITHUB_SHA"], describe)
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write(f"version={version}\n")
        output.write(f"tags={' '.join(tags)}\n")
    print(f"version={version}")
    print(f"tags={' '.join(tags)}")


if __name__ == "__main__":  # pragma: no cover
    main()
