"""Unit tests for the version and tags of images published by CI (T-24.2, #147)."""

import pytest

from scripts.image_metadata import image_metadata

SHA = "437b1b4f0a9c2d3e4f5a6b7c8d9e0f1a2b3c4d5e"


def test_push_to_main_publishes_main_and_the_commit_tag():
    version, tags = image_metadata("refs/heads/main", SHA, "v0.1.0-97-g437b1b4")

    assert version == "0.1.0-97-g437b1b4"
    assert tags == ["main", "sha-437b1b4"]


def test_release_tag_publishes_version_tags_latest_and_the_commit_tag():
    version, tags = image_metadata("refs/tags/v0.2.0", SHA, "v0.2.0")

    assert version == "0.2.0"
    assert tags == ["0.2.0", "0.2", "latest", "sha-437b1b4"]


def test_multi_digit_release_versions_are_kept():
    version, tags = image_metadata("refs/tags/v1.12.30", SHA, "v1.12.30")

    assert version == "1.12.30"
    assert tags[:2] == ["1.12.30", "1.12"]


@pytest.mark.parametrize(
    "ref",
    [
        "refs/heads/feature",
        "refs/pull/211/merge",
        "refs/tags/v0.2",
        "refs/tags/v0.2.0-rc1",
        "refs/tags/0.2.0",
        "refs/tags/v01.2.0",
        "refs/tags/release",
    ],
)
def test_other_refs_are_refused(ref):
    with pytest.raises(ValueError, match="published only from"):
        image_metadata(ref, SHA, "v0.1.0")


@pytest.mark.parametrize("sha", ["437b1b4", "", "Z" * 40])
def test_short_or_invalid_commit_is_refused(sha):
    with pytest.raises(ValueError, match="40-character"):
        image_metadata("refs/heads/main", sha, "v0.1.0")
