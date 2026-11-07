"""CI smoke tests: check the workflow contract that pull-request checks rely on."""

import os
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_FILE = ROOT / ".github" / "workflows" / "ci.yml"
DOCKERFILE = ROOT / "Dockerfile"
REQUIRED_CHECKS = {"Lint", "Tests", "E2E", "Container"}


@pytest.fixture(scope="module")
def workflow() -> dict:
    return yaml.safe_load(WORKFLOW_FILE.read_text(encoding="utf-8"))


def _triggers(workflow: dict) -> dict:
    # YAML 1.1 reads the bare key "on" as the boolean True.
    return workflow.get("on", workflow.get(True)) or {}


def test_workflow_runs_on_pull_requests_and_pushes_to_main(workflow):
    triggers = _triggers(workflow)

    assert "main" in triggers["pull_request"]["branches"]
    assert "main" in triggers["push"]["branches"]


def test_workflow_defines_required_check_jobs(workflow):
    job_names = {job.get("name") for job in workflow["jobs"].values()}

    assert REQUIRED_CHECKS <= job_names


def test_tests_job_fails_instead_of_skipping_without_database(workflow):
    tests_job = workflow["jobs"]["test"]

    assert tests_job["env"]["CI"] == "true"
    assert "TEST_DATABASE_URL" in tests_job["env"]


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
    assert "github.event_name == 'push'" in publish["if"]
    assert "github.ref == 'refs/heads/main'" in publish["if"]


def test_only_the_publish_job_can_write_packages(workflow):
    assert workflow["permissions"] == {"contents": "read"}
    writers = {
        job_id
        for job_id, job in workflow["jobs"].items()
        if job.get("permissions", {}).get("packages") == "write"
    }

    assert writers == {"publish"}
    assert "docker push" in " ".join(s.get("run", "") for s in workflow["jobs"]["publish"]["steps"])


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
