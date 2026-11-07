# US-01 automated tests

This document maps each acceptance criterion of US-01 (README §4.3) and each case of T-01.6 (#10) to the automated tests that verify it. All tests use synthetic accounts (`synthetic.*` and `e2e.*` logins and passwords), never real data. The unit and integration tests run in the `Tests` job of CI on every pull request; the browser end-to-end tests (T-01.7, #11) run with `pytest -m e2e` and are added to CI by T-23.3 (#140).

Run them locally against the test database (README §11):

```bash
pytest tests/test_security.py tests/integration
pytest -m e2e   # browser end-to-end tests
```

## Test modules

| Module | Tests | Scope |
| --- | --- | --- |
| `tests/test_security.py` | 7 | bcrypt hashing and verification |
| `tests/integration/test_staff_account.py` | 8 | staff account model and database constraints |
| `tests/integration/test_seed.py` | 7 | development seed command |
| `tests/integration/test_auth_sessions.py` | 15 | `/auth` login, logout and server-side sessions |
| `tests/integration/test_access.py` | 23 | reusable 401/403 dependencies |
| `tests/integration/test_csrf.py` | 23 | CSRF protection |
| `tests/integration/test_pages.py` | 44 | login pages, role-based navigation, browser errors |
| `tests/integration/test_us01_authentication.py` | 19 | cases added by T-01.6 (#10) |
| `tests/e2e/test_login_navigation.py` | 5 | browser end-to-end: login, navigation and logout per role (T-01.7, #11) |
| `tests/e2e/test_small_screen.py` | 4 | every page fits a 320 px screen without horizontal scrolling, per role and with a 64-character login (defect #202) |

## Acceptance criteria

| US-01 acceptance criterion | Verified by |
| --- | --- |
| An active account with valid credentials logs in and is granted access according to its role. | `test_auth_sessions.py::test_valid_login_creates_session_and_returns_account`; `test_pages.py::test_valid_login_redirects_to_the_home_page_of_the_account`; `test_pages.py::test_navigation_shows_exactly_the_areas_of_the_role` (each role); `test_us01_authentication.py::test_seeded_development_accounts_can_log_in_with_their_role` (each role); in a browser: `test_login_navigation.py::test_each_role_logs_in_navigates_its_areas_and_logs_out` (each role) |
| Invalid credentials or an inactive account are refused. | `test_auth_sessions.py::test_invalid_credentials_are_refused_with_the_same_message`, `::test_inactive_account_cannot_log_in`; `test_pages.py::test_invalid_credentials_show_the_same_error_with_401`, `::test_inactive_account_sees_the_same_error`; `test_us01_authentication.py::test_password_longer_than_72_bytes_is_refused_with_401` |
| An unauthenticated request to a protected route receives HTTP 401. | `test_access.py::test_requests_without_a_session_receive_401_not_403`, `::test_unknown_session_token_receives_401`, `::test_expired_session_receives_401`, `::test_deactivated_account_receives_401`; `test_pages.py::test_pages_without_a_session_show_the_login_page_with_401`; in a browser: `test_login_navigation.py::test_protected_page_without_a_session_shows_the_login_page` and the check after logout |
| An authenticated account without the required permission receives HTTP 403. | `test_access.py::test_role_access_matches_the_route_requirement` (each role); `test_pages.py::test_area_pages_follow_the_rbac_matrix` (every area for every role, against the RBAC matrix in README §3.2); `test_pages.py::test_api_clients_keep_json_responses`; in a browser: every area of another role returns "Access denied" with HTTP 403 (`test_login_navigation.py`) |

## Cases of T-01.6

| Case | Verified by |
| --- | --- |
| Password hashing | `test_security.py`: bcrypt with cost factor 12 (NFR-03 requires at least 10), no plain text in the hash, a new salt per hash, empty and over-72-byte passwords rejected; `test_staff_account.py::test_only_the_password_hash_is_stored` |
| Invalid credentials | Same message and HTTP 401 for wrong passwords, unknown logins and empty fields (API and pages); `test_us01_authentication.py::test_every_login_attempt_runs_one_bcrypt_check`: unknown logins still run one bcrypt check, so response times do not reveal which logins exist |
| Inactive accounts | Login refused (`test_auth_sessions.py`, `test_pages.py`); an existing session of a deactivated account is rejected and deleted (`test_auth_sessions.py::test_session_of_a_deactivated_account_is_rejected`, `test_access.py::test_deactivated_account_receives_401`) |
| Sessions | Only a SHA-256 hash of the token is stored; `HttpOnly`, `SameSite=Lax`, `Max-Age` of eight hours and `Secure` when configured; a new token on every login; logout deletes the session; expired and unknown sessions rejected (`test_auth_sessions.py`); the stored expiry is eight hours (`test_us01_authentication.py::test_new_session_expires_after_eight_hours`) |
| CSRF rejection | Missing, wrong, non-ASCII, pre-login and other-session tokens refused; cross-origin, `null` origin and cross-site fetches refused even with a valid token (`test_csrf.py`); every state-changing route of the application refuses requests without a token and accepts a valid one, and a new route that is not in the list fails the test (`test_us01_authentication.py::test_every_state_changing_route_*`); a page logout without a token keeps the session (`test_us01_authentication.py::test_page_logout_without_token_keeps_the_session`); the browser error page is titled by its reason, such as "Form expired" (`test_pages.py::test_expired_form_page_is_titled_form_expired`, `::test_error_page_title_matches_the_reason`, defect #204) |
| Allowed and denied role access | `test_access.py` (each role on routes for one and for several roles; 401 before 403); `test_pages.py::test_area_pages_follow_the_rbac_matrix` (15 area/role combinations) and `::test_navigation_shows_exactly_the_areas_of_the_role` |

## Tests fail when the behaviour breaks

Each rule was removed once from the application code to confirm that the tests detect it (mutation checks), in #7, #8, #13, #9 and #10. For this task: removing the dummy password check for unknown logins, lengthening the session to nine hours, removing the 72-byte guard, adding a `POST` route without listing it, and giving the seeded doctor the administrator role each make `test_us01_authentication.py` fail.

Expected values such as the areas per role and the seeded roles are written out in the tests instead of being read from the application code, so a wrong table in the code cannot make its own test pass.
