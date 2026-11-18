"""Compute the version, the channel and the image names of a CI build.

Used by .github/workflows/ci.yml (dev channel) and release.yml (rc and release channels).
The rules are in docs/versioning.md. Every tested build of ``main`` is pushed once as
``sha-<commit>``; the names returned in ``tags`` are then added to that same image, so a
promotion never rebuilds and never changes the commit tag (#224, #228).

Channels:

- ``dev``: a push to ``main``. The version is the next version after the latest tag on the
  commit's history, as a pre-release numbered by the workflow run: ``0.3.0-dev.57`` after
  ``v0.2.0``. After a release candidate ``vX.Y.Z-rc.N``, the next builds stay on
  ``X.Y.Z-dev.*``, because ``X.Y.Z`` has not been released yet.
- ``rc``: a tag ``vX.Y.Z-rc.N``; the version is ``X.Y.Z-rc.N``.
- ``release``: a tag ``vX.Y.Z``; the version is ``X.Y.Z``.

Any other ref or tag is refused, so an unexpected trigger can never publish an image.
"""

import os
import re
import subprocess
from typing import NamedTuple

MAIN_REF = "refs/heads/main"
NUMBER = r"(0|[1-9]\d*)"
VERSION_TAG = re.compile(rf"^v{NUMBER}\.{NUMBER}\.{NUMBER}(?:-rc\.([1-9]\d*))?$")
SHA = re.compile(r"^[0-9a-f]{40}$")


class Tag(NamedTuple):
    major: int
    minor: int
    patch: int
    rc: int | None  # None for a release

    @property
    def release(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"

    def sort_key(self) -> tuple[int, int, int, float]:
        # A release candidate sorts before the release of the same version.
        return (self.major, self.minor, self.patch, self.rc if self.rc else float("inf"))


class ImageMetadata(NamedTuple):
    version: str
    channel: str
    tags: list[str]  # names added to the tested image of the commit
    commit_tag: str  # the immutable name of that tested image


def parse_tag(name: str) -> Tag | None:
    """Return the parsed ``vX.Y.Z`` or ``vX.Y.Z-rc.N`` tag, or None for any other name."""
    match = VERSION_TAG.match(name)
    if not match:
        return None
    major, minor, patch, rc = match.groups()
    return Tag(int(major), int(minor), int(patch), int(rc) if rc else None)


def latest_tag(names: list[str]) -> Tag | None:
    """Return the highest version tag among ``names``, ignoring names of any other form."""
    tags = [tag for tag in map(parse_tag, names) if tag is not None]
    return max(tags, key=Tag.sort_key, default=None)


def next_dev_version(latest: Tag | None, run_number: int) -> str:
    if latest is None:
        base = "0.1.0"
    elif latest.rc is not None:
        base = latest.release  # X.Y.Z is not released yet: keep developing it
    else:
        base = f"{latest.major}.{latest.minor + 1}.0"
    return f"{base}-dev.{run_number}"


def image_metadata(ref: str, sha: str, tag_names: list[str], run_number: str) -> ImageMetadata:
    """Return the version, channel and image tags for a build of ``sha`` triggered by ``ref``.

    ``tag_names`` are the tags reachable from the commit; ``run_number`` numbers dev builds.
    """
    if not SHA.match(sha):
        raise ValueError(f"Expected a full 40-character commit SHA, got {sha!r}.")
    commit_tag = f"sha-{sha[:7]}"

    if ref == MAIN_REF:
        if not run_number.isdigit():
            raise ValueError(f"Expected a workflow run number, got {run_number!r}.")
        version = next_dev_version(latest_tag(tag_names), int(run_number))
        return ImageMetadata(version, "dev", [version, "dev"], commit_tag)

    tag = parse_tag(ref.removeprefix("refs/tags/")) if ref.startswith("refs/tags/") else None
    if tag is None:
        raise ValueError(
            f"Images are published only from {MAIN_REF} or tags vMAJOR.MINOR.PATCH and "
            f"vMAJOR.MINOR.PATCH-rc.N, not from {ref!r}."
        )
    if tag.rc is not None:
        version = f"{tag.release}-rc.{tag.rc}"
        return ImageMetadata(version, "rc", [version, "rc"], commit_tag)
    minor_line = f"{tag.major}.{tag.minor}"
    return ImageMetadata(tag.release, "release", [tag.release, minor_line, "latest"], commit_tag)


def main() -> None:  # pragma: no cover - runs in the CI job
    tag_names = subprocess.run(
        ["git", "tag", "--merged", "HEAD", "--list", "v*"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    metadata = image_metadata(
        os.environ["GITHUB_REF"],
        os.environ["GITHUB_SHA"],
        tag_names,
        os.environ.get("GITHUB_RUN_NUMBER", ""),
    )
    lines = [
        f"version={metadata.version}",
        f"channel={metadata.channel}",
        f"tags={' '.join(metadata.tags)}",
        f"commit_tag={metadata.commit_tag}",
    ]
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
        output.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":  # pragma: no cover
    main()
