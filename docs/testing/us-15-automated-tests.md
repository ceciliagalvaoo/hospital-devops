# US-15 automated tests

This document maps each acceptance criterion of US-15, deactivate a staff account ([backlog.md](../backlog.md) §3), and each case of T-15.3 (#22) to the automated tests that verify it. All tests use synthetic accounts and passwords, never real data. They run in the `Tests` job of CI on every pull request.

Run them locally against the test database ([testing.md](../development/testing.md)):

```bash
pytest tests/integration/test_staff_account_deactivation.py tests/integration/test_staff_pages.py tests/integration/test_us15_account_deactivation.py
```

## Test modules

| Module | Tests | Scope |
| --- | --- | --- |
| `tests/integration/test_staff_account_deactivation.py` | 8 | `POST /api/staff/<id>/deactivate`: sessions ended, other sessions kept, an inactive account, the own account, unknown accounts, access (T-15.1, #20) |
| `tests/integration/test_staff_pages.py` | 13 of 25 | the Action column, the confirmation page, the result in the list, an inactive account, the own account, access (T-15.2, #21) |
| `tests/integration/test_us15_account_deactivation.py` | 37 | acceptance and access cases of T-15.3 (#22), each deactivation through the API and the page |
| `tests/integration/test_us01_authentication.py` | (shared) | both deactivation routes refuse requests without a CSRF token; inactive accounts were refused at login and on every request since US-01 |

## Acceptance criteria

| US-15 acceptance criterion | Verified by |
| --- | --- |
| Given an active staff account, when an administrator deactivates it, then later login attempts are refused and requests through existing sessions are rejected. | `test_us15_account_deactivation.py::test_existing_sessions_are_rejected_after_deactivation` (each role; two sessions opened through the API and the login page; afterwards both get HTTP 401 from a protected API request and a protected page, and no session remains), `::test_later_logins_are_refused_like_wrong_passwords` (through the API and the login page, HTTP 401 with the same message as a wrong password, no session created); `::test_other_accounts_and_the_administrator_keep_their_sessions`, `::test_the_account_and_its_doctor_profile_are_kept`, `::test_deactivating_an_inactive_account_changes_nothing`, `::test_administrators_cannot_deactivate_their_own_account` (HTTP 409); `test_staff_pages.py::test_confirming_deactivates_and_shows_the_list_with_a_confirmation`, `::test_the_confirmation_explains_the_effect_and_changes_nothing` |
| Given a receptionist or doctor, when they attempt to deactivate a staff account, then the system refuses the action. | `test_us15_account_deactivation.py::test_receptionists_and_doctors_are_refused` (API and page, HTTP 403, for a target of each role; the target stays active and its session keeps working), `::test_receptionists_and_doctors_cannot_open_the_confirmation`, `::test_receptionists_and_doctors_cannot_deactivate_themselves`; `test_staff_pages.py::test_only_administrators_open_the_staff_pages` |

## Cases of T-15.3

| Case | Verified by |
| --- | --- |
| Denied login | criterion 1 above: `::test_later_logins_are_refused_like_wrong_passwords` |
| Rejection of existing sessions after deactivation | criterion 1 above: `::test_existing_sessions_are_rejected_after_deactivation` |
| Role restrictions | criterion 2 above; without a valid session ([requirements.md](../requirements.md) §2.4): `test_us15_account_deactivation.py::test_deactivation_without_a_session_is_refused` (API HTTP 401, page HTTP 401 with the login page), `::test_a_deactivated_administrator_can_no_longer_deactivate` |

## Mutation checks

Each of these faults in the application code made tests of `test_us15_account_deactivation.py` fail: inactive accounts allowed to log in; sessions neither deleted nor checked for an active account; the confirmation page deactivating nothing; doctors allowed to deactivate on the page; a deactivation that also ends every other session; inactive accounts answered differently from a wrong password.
