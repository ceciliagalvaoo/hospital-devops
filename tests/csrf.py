"""Helpers for tests that send state-changing requests through the CSRF check."""

from app.csrf import CSRF_HEADER


def csrf_headers(client) -> dict[str, str]:
    """Fetch the current CSRF token for the client's cookies and return it as a header."""
    return {CSRF_HEADER: client.get("/auth/csrf").json()["csrf_token"]}
