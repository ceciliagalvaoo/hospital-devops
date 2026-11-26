# US-14 automated tests

This document maps each acceptance criterion of US-14, create staff accounts ([backlog.md](../backlog.md) §3), and each case of T-14.3 (#17) to the automated tests that verify it. All tests use synthetic accounts and passwords, never real data. They run in the `Tests` job of CI on every pull request.

Run them locally against the test database ([testing.md](../development/testing.md)):

```bash
pytest tests/test_account_rules.py tests/integration/test_staff_account_creation.py tests/integration/test_staff_pages.py tests/integration/test_us14_staff_account_creation.py
```

## Test modules

| Module | Tests | Scope |
| --- | --- | --- |
| `tests/test_account_rules.py` | 21 | account rules: lower-case logins, login format, roles, password length and confirmation (T-14.1, #15) |
| `tests/integration/test_staff_account_creation.py` | 14 | `POST /api/staff`, case-insensitive logins at login, a login taken during creation (T-14.1, #15) |
| `tests/integration/test_staff_pages.py` | 12 | the staff accounts area and the creation form: list, confirmation, passwords never sent back, `autocomplete` (T-14.2, #16) |
| `tests/integration/test_us14_staff_account_creation.py` | 41 | acceptance and access cases of T-14.3 (#17), each through the API and the page |
| `tests/integration/test_us01_authentication.py` | (shared) | both creation routes refuse requests without a CSRF token |

## Acceptance criteria

| US-14 acceptance criterion | Verified by |
| --- | --- |
| Given an authenticated administrator, a unique login and one of the three supported roles, when the account is created, then the password is stored as a bcrypt hash and the new user can log in with the assigned role. | `test_us14_staff_account_creation.py::test_a_new_account_has_a_bcrypt_hash_and_logs_in_with_its_role` (each role, API and page; the stored hash starts with `$2b$12$` and does not contain the password; the new account logs in and gets its role), `::test_the_new_account_sees_the_areas_of_its_role`; `test_staff_pages.py::test_creating_an_account_shows_it_in_the_list_with_a_confirmation` |
| Given a duplicate login or an unsupported role, when account creation is submitted, then the system rejects it. | `test_us14_staff_account_creation.py::test_a_duplicate_login_is_rejected_in_any_case` (the same login in three cases; the existing account unchanged), `::test_an_unsupported_role_is_rejected` (empty, `patient`, `nurse`, `Administrator`, `root`); API and page, HTTP 422, nothing created; `test_staff_account_creation.py::test_a_login_taken_between_the_check_and_the_insert_is_reported` |
| Given a receptionist or doctor, when they attempt to create a staff account, then the system refuses the action. | `test_us14_staff_account_creation.py::test_receptionists_and_doctors_are_refused` (API and page, HTTP 403, nothing created); `test_staff_pages.py::test_only_administrators_open_the_staff_pages` (the list, the form and the submission) |

## Cases of T-14.3

| Case | Verified by |
| --- | --- |
| Duplicate logins | criterion 2 above; logins are compared in lower case, so a duplicate in another case is refused |
| Invalid roles | criterion 2 above; `test_account_rules.py::test_every_role_is_supported_and_others_are_not` |
| Password hashing | criterion 1 above (bcrypt, cost factor 12, NFR-03 requires at least 10); `test_us14_staff_account_creation.py::test_invalid_logins_and_passwords_are_rejected` (missing and short passwords, invalid logins); `test_staff_pages.py::test_invalid_data_keeps_login_and_role_but_never_the_passwords` |
| Denied access for other roles | criterion 3 above; without a valid session ([requirements.md](../requirements.md) §2.4): `test_us14_staff_account_creation.py::test_creation_without_a_session_is_refused` (API HTTP 401, page HTTP 401 with the login page), `::test_a_deactivated_administrator_can_no_longer_create_accounts` |

## Mutation checks

Each of these faults in the application code made tests of `test_us14_staff_account_creation.py` fail: receptionists allowed in the API; doctors allowed on the pages; duplicates checked as typed instead of in lower case; any role accepted; a bcrypt cost factor of 4 instead of 12.
