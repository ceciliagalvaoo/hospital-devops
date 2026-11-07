"""Throwaway test for #143: a failing test and a lint error. This file is never merged."""

import os  # unused on purpose: Ruff reports F401, so the Lint check fails


def test_deliberate_failure_for_143():
    assert False, "Deliberate failure for the blocked-merge check of #143."
