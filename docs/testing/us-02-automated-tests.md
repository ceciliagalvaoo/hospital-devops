# US-02 automated tests

This document maps each acceptance criterion of US-02, register a doctor ([backlog.md](../backlog.md) §3), and each case of T-02.4 (#58) to the automated tests that verify it. All tests use synthetic accounts and synthetic doctor names, never real data. They run in the `Tests` job of CI on every pull request.

Run them locally against the test database ([testing.md](../development/testing.md)):

```bash
pytest tests/test_doctor_rules.py tests/integration/test_doctor.py tests/integration/test_doctor_registration.py tests/integration/test_doctor_pages.py tests/integration/test_us02_doctor_registration.py
```

## Test modules

| Module | Tests | Scope |
| --- | --- | --- |
| `tests/integration/test_doctor.py` | 14 | doctor and availability models, migration and database constraints (T-02.1, #55) |
| `tests/test_doctor_rules.py` | 21 | weekly availability rules: at least one range, half-hour times, end after start, no overlap on the same day, errors by row in row order (T-02.2, #56) |
| `tests/integration/test_doctor_registration.py` | 18 | eligible accounts, name and specialisation rules, `POST /api/doctors` (T-02.2, #56) |
| `tests/integration/test_doctor_pages.py` | 19 | the doctors area, the registration form with its availability rows, the profile (T-02.3, #57) |
| `tests/integration/test_us02_doctor_registration.py` | 41 | acceptance and access cases of T-02.4 (#58), each through the API and the page |
| `tests/integration/test_us01_authentication.py` | (shared) | both registration routes refuse requests without a CSRF token |

## Acceptance criteria

| US-02 acceptance criterion | Verified by |
| --- | --- |
| Given an authenticated administrator and valid doctor details, specialisation and availability, when registration is submitted, then the doctor is saved as active and linked to a doctor staff account. | `test_us02_doctor_registration.py::test_a_valid_doctor_is_saved_active_and_linked_to_the_doctor_account` (API and page; the database holds the name, the specialisation, `is_active`, the doctor account and the weekly ranges), `::test_the_saved_doctor_is_shown_on_its_profile_and_in_the_doctors_area`, `::test_adjacent_ranges_are_valid`; `test_doctor_pages.py::test_registration_shows_the_profile_with_a_confirmation` |
| Given missing required details or invalid availability, when registration is submitted, then the system rejects it and identifies the invalid fields. | `test_us02_doctor_registration.py::test_missing_required_details_are_rejected_and_identified` (account, name, specialisation, no range), `::test_invalid_availability_is_rejected_and_its_row_identified` (an incomplete range, an unknown weekday, a time off the half hour, an end before the start, an overlap; each identified by its row); API and page, HTTP 422, nothing saved; `test_doctor_pages.py::test_invalid_data_keeps_the_values_and_identifies_every_field_and_row` (summary in form order, row messages, focus) |
| Given a receptionist or doctor, when they attempt to register a doctor, then the system refuses the action. | `test_us02_doctor_registration.py::test_receptionists_and_doctors_are_refused` (API and page, HTTP 403, nothing saved), `::test_receptionists_and_doctors_cannot_open_the_form`; `test_doctor_pages.py::test_only_administrators_open_the_doctor_pages` (the area, the form and the profile) |

## Cases of T-02.4

| Case | Verified by |
| --- | --- |
| Registration | criterion 1 above |
| Invalid availability | criterion 2 above; `test_doctor_rules.py` (every rule, empty rows ignored, row numbers kept, every invalid row reported in row order); `test_doctor.py::test_malformed_ranges_are_rejected_by_the_database` |
| Account association | `test_us02_doctor_registration.py::test_only_an_active_doctor_account_can_be_linked` (receptionist, administrator and inactive doctor accounts refused), `::test_an_account_is_linked_to_one_doctor_only`; `test_doctor_registration.py::test_only_active_doctor_accounts_without_a_profile_are_eligible`; `test_doctor.py::test_an_account_has_at_most_one_doctor_profile`, `::test_an_account_with_a_doctor_profile_cannot_be_deleted` |
| Denied access | criterion 3 above; without a valid session ([requirements.md](../requirements.md) §2.4): `test_us02_doctor_registration.py::test_registration_without_a_session_is_refused` (API HTTP 401, page HTTP 401 with the login page), `::test_a_deactivated_administrator_can_no_longer_register` |

## Mutation checks

Each of these faults in the application code made tests of `test_us02_doctor_registration.py` fail: receptionists allowed in the API; doctors allowed on the pages; inactive doctor accounts eligible; no overlap check; the availability not saved; the profile linked to the administrator's own account instead of the chosen one.
