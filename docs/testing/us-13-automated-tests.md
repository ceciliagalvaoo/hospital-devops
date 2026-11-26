# US-13 automated tests

This document maps each acceptance criterion of US-13, update doctor details ([backlog.md](../backlog.md) §3), and each case of T-13.3 (#64) to the automated tests that verify it. All tests use synthetic accounts and synthetic doctor names, never real data. They run in the `Tests` job of CI on every pull request.

Run them locally against the test database ([testing.md](../development/testing.md)):

```bash
pytest tests/test_doctor_rules.py tests/integration/test_doctor_update.py tests/integration/test_doctor_pages.py tests/integration/test_us13_doctor_update.py
```

## Test modules

| Module | Tests | Scope |
| --- | --- | --- |
| `tests/test_doctor_rules.py` | 3 of 24 | the update rules, which are the registration rules for the name, the specialisation and the availability (T-13.1, #62) |
| `tests/integration/test_doctor_update.py` | 7 | `POST /api/doctors/<id>`: the ranges replaced, the account kept, errors, unknown doctors, access (T-13.1, #62) |
| `tests/integration/test_doctor_pages.py` | 12 of 31 | the edit form: current values, more ranges than rows, the confirmation, errors kept and identified, access (T-13.2, #63) |
| `tests/integration/test_us13_doctor_update.py` | 43 | acceptance and access cases of T-13.3 (#64), each through the API and the page |
| `tests/integration/test_us01_authentication.py` | (shared) | both update routes refuse requests without a CSRF token |

## Acceptance criteria

| US-13 acceptance criterion | Verified by |
| --- | --- |
| Given an authenticated administrator and valid changes, when doctor details or availability are saved, then the changes are persisted and existing appointments are retained. | `test_us13_doctor_update.py::test_valid_changes_are_persisted` (API and page; the database holds the new name, specialisation and ranges, and the previous ranges are gone), `::test_the_changes_are_shown_after_a_reload`, `::test_adjacent_ranges_are_valid`; `test_doctor_pages.py::test_saving_shows_the_profile_with_a_confirmation`. Appointments do not exist yet (US-04, Sprint 3): `::test_an_update_keeps_the_doctor_its_account_and_its_status` checks that an update keeps the doctor's id, its account link (even when another account is submitted) and its status, active or inactive, and changes no other doctor; the retention of appointments is to be tested when US-04 is integrated. |
| Given invalid availability, when the change is submitted, then the system rejects it and identifies the invalid fields. | `test_us13_doctor_update.py::test_invalid_availability_is_rejected_and_its_row_identified` (an incomplete range, an unknown weekday, a time off the half hour, an end before the start, an overlap; each identified by its row), `::test_missing_or_invalid_details_are_rejected_and_identified` (no name, a name too long, an unknown specialisation, no range), `::test_every_invalid_field_is_identified_at_once`; API and page, HTTP 422, nothing changed; `test_doctor_pages.py::test_invalid_changes_keep_the_values_and_identify_every_field_and_row` |
| Given a receptionist or doctor, when they attempt to update doctor details, then the system refuses the action. | `test_us13_doctor_update.py::test_receptionists_and_doctors_are_refused` (API and page, HTTP 403, nothing changed), `::test_a_doctor_cannot_update_its_own_profile`, `::test_receptionists_and_doctors_cannot_open_the_edit_form`; `test_doctor_pages.py::test_only_administrators_open_the_doctor_pages` |

## Cases of T-13.3

| Case | Verified by |
| --- | --- |
| Persistence | criterion 1 above |
| Invalid availability | criterion 2 above; `test_doctor_rules.py` (the availability rules shared with registration) |
| Denied access for other roles | criterion 3 above; without a valid session ([requirements.md](../requirements.md) §2.4): `test_us13_doctor_update.py::test_updates_without_a_session_are_refused` (API HTTP 401, page HTTP 401 with the login page), `::test_a_deactivated_administrator_can_no_longer_update`; an unknown doctor: `::test_an_unknown_doctor_is_not_found` (HTTP 404) |

## Mutation checks

Each of these faults in the application code made tests of `test_us13_doctor_update.py` fail: doctors allowed on the edit page; an update that reactivates an inactive doctor; the API taking the staff account from the submitted form; no overlap check in updates; the edit page saving the name before validating; the previous ranges kept next to the new ones.
