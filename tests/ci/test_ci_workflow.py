"""CI smoke tests: check the workflow contract that pull-request checks rely on."""

import os
import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_FILE = ROOT / ".github" / "workflows" / "ci.yml"
DOCKERFILE = ROOT / "Dockerfile"
REQUIRED_CHECKS = {"Lint", "Tests", "Container"}


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


def test_workflow_uses_application_image_python_version(workflow):
    image = re.search(r"^FROM python:(\d+\.\d+)", DOCKERFILE.read_text(encoding="utf-8"), re.M)

    assert image is not None
    assert workflow["env"]["PYTHON_VERSION"] == image.group(1)


@pytest.mark.skipif(
    os.environ.get("CI_FORCE_FAILURE") != "true",
    reason="Deliberate failure runs only when CI_FORCE_FAILURE=true (manual CI run).",
)
def test_deliberate_failure_marks_check_as_failed():
    pytest.fail("Deliberate failure requested with CI_FORCE_FAILURE=true.")
