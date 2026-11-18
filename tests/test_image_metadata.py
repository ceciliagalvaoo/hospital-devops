"""Unit tests for the version, channel and tags of images published by CI (#147, #227)."""

import pytest

from scripts.image_metadata import Tag, image_metadata, latest_tag, parse_tag

SHA = "437b1b4f0a9c2d3e4f5a6b7c8d9e0f1a2b3c4d5e"
MAIN = "refs/heads/main"


# ---------------------------------------------------------------- dev channel (push to main)


@pytest.mark.parametrize(
    ("tags", "expected"),
    [
        (["v0.1.0", "v0.2.0"], "0.3.0-dev.57"),  # next minor after the latest release
        (["v0.2.0", "v0.2.1"], "0.3.0-dev.57"),  # a patch release counts as well
        (["v0.2.0", "v0.3.0-rc.1"], "0.3.0-dev.57"),  # after an rc: 0.3.0 is not released
        (["v0.3.0-rc.1", "v0.3.0-rc.2", "v0.3.0"], "0.4.0-dev.57"),
        (["v1.9.0", "v1.10.0"], "1.11.0-dev.57"),  # compared as numbers, not as text
        ([], "0.1.0-dev.57"),  # no release yet
    ],
)
def test_main_builds_get_the_next_development_version(tags, expected):
    metadata = image_metadata(MAIN, SHA, tags, "57")

    assert metadata.version == expected
    assert metadata.channel == "dev"


def test_main_builds_keep_their_image_tags():
    # The dev image names are changed with the promotion in #228.
    assert image_metadata(MAIN, SHA, ["v0.2.0"], "57").tags == ["main", "sha-437b1b4"]


def test_tags_of_other_forms_do_not_count_for_the_next_version():
    # v0.1.0-rc1 is the throw-away tag of Lab 4; v9.9 and beta tags are not ours.
    tags = ["v0.2.0", "v0.1.0-rc1", "v9.9", "v9.0.0-beta.1", "release-9"]

    assert image_metadata(MAIN, SHA, tags, "57").version == "0.3.0-dev.57"


@pytest.mark.parametrize("run_number", ["", "abc", "-1"])
def test_main_builds_need_a_run_number(run_number):
    with pytest.raises(ValueError, match="run number"):
        image_metadata(MAIN, SHA, ["v0.2.0"], run_number)


# ---------------------------------------------------------------- rc and release channels


def test_release_candidate_tag():
    metadata = image_metadata("refs/tags/v0.2.1-rc.1", SHA, [], "")

    assert metadata == ("0.2.1-rc.1", "rc", ["0.2.1-rc.1", "rc"])


def test_release_tag():
    metadata = image_metadata("refs/tags/v0.2.1", SHA, [], "")

    assert metadata == ("0.2.1", "release", ["0.2.1", "0.2", "latest", "sha-437b1b4"])


def test_multi_digit_release_versions_are_kept():
    metadata = image_metadata("refs/tags/v1.12.30", SHA, [], "")

    assert metadata.version == "1.12.30"
    assert metadata.tags[:2] == ["1.12.30", "1.12"]


@pytest.mark.parametrize(
    "ref",
    [
        "refs/heads/feature",
        "refs/pull/211/merge",
        "refs/tags/v0.2",
        "refs/tags/v0.2.0-rc1",
        "refs/tags/v0.2.0-rc.0",
        "refs/tags/v0.2.0-rc.01",
        "refs/tags/v0.2.0-beta.1",
        "refs/tags/0.2.0",
        "refs/tags/v01.2.0",
        "refs/tags/release",
    ],
)
def test_other_refs_and_malformed_tags_are_refused(ref):
    with pytest.raises(ValueError, match="published only from"):
        image_metadata(ref, SHA, ["v0.2.0"], "57")


@pytest.mark.parametrize("sha", ["437b1b4", "", "Z" * 40])
def test_short_or_invalid_commit_is_refused(sha):
    with pytest.raises(ValueError, match="40-character"):
        image_metadata(MAIN, sha, ["v0.2.0"], "57")


# ---------------------------------------------------------------- ordering


def test_release_candidates_sort_before_their_release():
    ordered = ["v0.3.0-rc.1", "v0.3.0-rc.2", "v0.3.0-rc.10", "v0.3.0", "v0.3.1"]

    assert sorted(map(parse_tag, reversed(ordered)), key=Tag.sort_key) == list(
        map(parse_tag, ordered)
    )


def test_latest_tag_of_no_version_tags_is_none():
    assert latest_tag(["release", "v1"]) is None
