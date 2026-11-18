"""CI smoke tests: check the workflow contract that pull-request checks rely on."""

import configparser
import os
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_FILE = ROOT / ".github" / "workflows" / "ci.yml"
RELEASE_FILE = ROOT / ".github" / "workflows" / "release.yml"
DOCKERFILE = ROOT / "Dockerfile"
COVERAGE_CONFIG = ROOT / ".coveragerc"
REQUIRED_CHECKS = {"Lint", "Tests", "E2E", "Container"}
DOCKER_BUILD = re.compile(r"docker build(?!x)")  # an image build, not "docker buildx imagetools"


@pytest.fixture(scope="module")
def workflow() -> dict:
    return yaml.safe_load(WORKFLOW_FILE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def release() -> dict:
    return yaml.safe_load(RELEASE_FILE.read_text(encoding="utf-8"))


def _commands(job: dict) -> str:
    return " ".join(step.get("run", "") for step in job["steps"])


def _triggers(workflow: dict) -> dict:
    # YAML 1.1 reads the bare key "on" as the boolean True.
    return workflow.get("on", workflow.get(True)) or {}


def test_workflow_runs_on_pull_requests_and_pushes_to_main_but_not_on_tags(workflow):
    # Tags are handled by release.yml; building on a tag would publish an untested rebuild.
    triggers = _triggers(workflow)

    assert "main" in triggers["pull_request"]["branches"]
    assert "main" in triggers["push"]["branches"]
    assert "tags" not in triggers["push"]


def test_workflow_defines_required_check_jobs(workflow):
    job_names = {job.get("name") for job in workflow["jobs"].values()}

    assert REQUIRED_CHECKS <= job_names


def test_tests_job_fails_instead_of_skipping_without_database(workflow):
    tests_job = workflow["jobs"]["test"]

    assert tests_job["env"]["CI"] == "true"
    assert "TEST_DATABASE_URL" in tests_job["env"]


def test_coverage_gate_requires_every_line_and_branch_of_the_application():
    config = configparser.ConfigParser()
    config.read(COVERAGE_CONFIG, encoding="utf-8")

    assert config["run"]["source"] == "app"
    assert config["run"].getboolean("branch") is True
    assert float(config["report"]["fail_under"]) == 100


def test_tests_job_measures_coverage_of_the_application_so_the_gate_applies(workflow):
    commands = " ".join(step.get("run", "") for step in workflow["jobs"]["test"]["steps"])

    assert "--cov=app" in commands
    assert "--cov-fail-under" not in commands  # one threshold, in .coveragerc
    assert "--no-cov" not in commands


def test_e2e_job_runs_browser_tests_and_keeps_artifacts_of_failures(workflow):
    e2e_job = workflow["jobs"]["e2e"]
    steps = e2e_job["steps"]
    commands = " ".join(step.get("run", "") for step in steps)
    upload = next(step for step in steps if "upload-artifact" in step.get("uses", ""))

    assert e2e_job["env"]["CI"] == "true"
    assert "TEST_DATABASE_URL" in e2e_job["env"]
    assert "playwright install" in commands and "chromium" in commands
    assert "pytest -m e2e" in commands
    assert "--tracing retain-on-failure" in commands
    assert upload["if"] == "failure()"
    assert upload["with"]["name"] == "playwright-results"


def test_publish_job_runs_only_on_main_after_all_required_checks(workflow):
    publish = workflow["jobs"]["publish"]
    check_jobs = {
        job_id for job_id, job in workflow["jobs"].items() if job.get("name") in REQUIRED_CHECKS
    }

    assert set(publish["needs"]) == check_jobs
    assert publish["if"] == "github.event_name == 'push' && github.ref == 'refs/heads/main'"
    assert publish["environment"] == "test"


def test_container_job_builds_the_image_once_and_smoke_tests_that_image(workflow):
    container = workflow["jobs"]["container"]
    commands = _commands(container)
    smoke = next(step for step in container["steps"] if "pytest -m smoke" in step.get("run", ""))
    upload = next(s for s in container["steps"] if "upload-artifact" in s.get("uses", ""))

    assert container["steps"][0]["with"]["fetch-depth"] == 0
    assert "python scripts/image_metadata.py" in commands
    assert len(DOCKER_BUILD.findall(commands)) == 1
    assert '--build-arg VCS_REF="$GITHUB_SHA"' in commands
    assert "--tag hospital-devops:ci" in commands
    assert smoke["env"]["SMOKE_IMAGE"] == "hospital-devops:ci"
    assert upload["with"]["name"] == "tested-image"


def test_publish_job_pushes_the_tested_image_without_building(workflow):
    commands = _commands(workflow["jobs"]["publish"])

    assert not DOCKER_BUILD.search(commands)
    assert "docker load" in commands
    assert 'docker push "$IMAGE_NAME:build-$COMMIT_TAG"' in commands
    assert "docker buildx imagetools create" in commands
    assert "does not match" in commands  # every name is checked against the tested digest


def test_only_the_publishing_jobs_can_write_packages(workflow, release):
    assert workflow["permissions"] == {"contents": "read"}
    assert release["permissions"] == {"contents": "read"}
    writers = {
        f"{name}:{job_id}"
        for name, flow in (("ci", workflow), ("release", release))
        for job_id, job in flow["jobs"].items()
        if job.get("permissions", {}).get("packages") == "write"
    }

    assert writers == {"ci:publish", "release:promote"}


def test_verify_image_job_checks_the_published_commit_without_credentials(workflow):
    verify = workflow["jobs"]["verify-image"]
    commands = " ".join(step.get("run", "") for step in verify["steps"])

    assert verify["needs"] == ["publish"]
    assert verify["if"] == workflow["jobs"]["publish"]["if"]
    assert "permissions" not in verify
    assert "docker login" not in commands
    assert 'PUBLISHED_IMAGE="$IMAGE_NAME:sha-${GITHUB_SHA::7}"' in commands
    assert "pytest -m published" in commands
    assert verify["env"]["EXPECTED_REVISION"] == "${{ github.sha }}"
    assert verify["env"]["EXPECTED_VERSION"] == "${{ needs.publish.outputs.version }}"


def test_release_workflow_runs_only_on_version_tags(release):
    triggers = _triggers(release)

    assert triggers == {"push": {"tags": ["v*"]}}
    assert release["concurrency"]["cancel-in-progress"] is False


def test_release_workflow_promotes_without_building(release):
    commands = " ".join(_commands(job) for job in release["jobs"].values())

    assert not DOCKER_BUILD.search(commands)
    assert "docker push" not in commands
    assert "docker buildx imagetools create" in commands


def test_release_fails_for_a_commit_without_a_tested_image(release):
    promote = release["jobs"]["promote"]
    check = next(s for s in promote["steps"] if "tested image" in s.get("name", ""))

    assert promote["needs"] == "version"
    assert 'imagetools inspect "$IMAGE_NAME:$COMMIT_TAG"' in check["run"]
    assert "exit 1" in check["run"]


def test_releases_need_the_approval_of_the_production_environment(release):
    environment = release["jobs"]["promote"]["environment"]

    assert environment == (
        "${{ needs.version.outputs.channel == 'release' && 'production' || 'test' }}"
    )


def test_only_the_github_release_job_can_write_to_the_repository(release):
    writers = {
        job_id
        for job_id, job in release["jobs"].items()
        if job.get("permissions", {}).get("contents") == "write"
    }
    github_release = release["jobs"]["github-release"]

    assert writers == {"github-release"}
    assert set(github_release["needs"]) == {"version", "promote"}
    assert "--generate-notes" in _commands(github_release)
    assert "--prerelease" in _commands(github_release)


def test_runs_on_main_are_not_cancelled_by_newer_runs(workflow):
    assert (
        workflow["concurrency"]["cancel-in-progress"]
        == "${{ github.event_name == 'pull_request' }}"
    )


def test_workflow_uses_application_image_python_version(workflow):
    image = re.search(
        r"^ARG PYTHON_IMAGE=python:(\d+\.\d+)\.\d+", DOCKERFILE.read_text(encoding="utf-8"), re.M
    )

    assert image is not None
    assert workflow["env"]["PYTHON_VERSION"] == image.group(1)


@pytest.mark.skipif(
    os.environ.get("CI_FORCE_FAILURE") != "true",
    reason="Deliberate failure runs only when CI_FORCE_FAILURE=true (manual CI run).",
)
def test_deliberate_failure_marks_check_as_failed():
    pytest.fail("Deliberate failure requested with CI_FORCE_FAILURE=true.")
