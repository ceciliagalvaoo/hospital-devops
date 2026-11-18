# US-03 automated tests

This document maps each acceptance criterion of US-03, register a patient ([backlog.md](../backlog.md) §3), and each case of T-03.4 (#34) to the automated tests that verify it. All tests use synthetic accounts and synthetic patients (`Synthetic Patient`, `example.test` addresses), never real patient information. The unit and integration tests run in the `Tests` job of CI on every pull request; the browser end-to-end tests (T-03.5, #35) run with `pytest -m e2e` in the `E2E` job.

Run them locally against the test database ([testing.md](../development/testing.md)):

```bash
pytest tests/test_patient_rules.py tests/integration/test_patient.py tests/integration/test_patient_api.py tests/integration/test_patient_pages.py tests/integration/test_us03_patient_registration.py
pytest -m e2e tests/e2e/test_patient_registration.py   # browser end-to-end tests
```

## Test modules

| Module | Tests | Scope |
| --- | --- | --- |
| `tests/integration/test_patient.py` | 8 | patient model, migration and database constraints (T-03.1, #31) |
| `tests/test_patient_rules.py` | 29 | registration rules: required fields, length, dates, phone and e-mail formats (T-03.2, #32) |
| `tests/integration/test_patient_api.py` | 5 | `POST /api/patients` (T-03.2, #32) |
| `tests/integration/test_patient_pages.py` | 10 | registration form and record page: labels, error summary, values kept, focus (T-03.3, #33) |
| `tests/integration/test_us03_patient_registration.py` | 36 | acceptance and access cases of T-03.4 (#34), each through the API and the page |
| `tests/e2e/test_patient_registration.py` | 3 | browser end-to-end: register a patient and display the saved record, for receptionists and administrators; doctors refused (T-03.5, #35) |
| `tests/e2e/test_small_screen.py` | (shared) | the registration form fits a 320 px screen for every role |

## Acceptance criteria

| US-03 acceptance criterion | Verified by |
| --- | --- |
| Given an authenticated receptionist and valid patient information, when registration is submitted, then the patient is saved and can be found through patient search. | Saved: `test_us03_patient_registration.py::test_valid_patient_is_saved_with_every_field` (receptionist and administrator, API and page, every field read back from the database), `::test_only_name_and_date_of_birth_are_needed`, `::test_each_registration_gets_its_own_record_number`, `::test_saved_patient_is_shown_on_its_record`; in a browser: `test_patient_registration.py::test_register_a_patient_and_display_the_saved_record` (receptionist and administrator: from the navigation to the form, the empty form rejected with both fields identified and the focus on the name, the corrected form saved, the record displayed with its confirmation, and a reload that does not register the patient twice). Found through search: `test_us09_patient_search.py::test_a_patient_registered_on_the_page_is_found_by_search` (a patient registered on the page is found by its name and its record number, through the API and the page; T-09.3, #40); in a browser: `test_search_and_open_patient.py::test_register_search_and_open_the_correct_record` (T-09.4, #41). |
| Given a missing required name or date of birth, when registration is submitted, then the system rejects it and identifies the missing fields. | `test_us03_patient_registration.py::test_missing_required_fields_are_rejected_and_identified` (name, blank name, date of birth and both; API and page; HTTP 422, exactly the missing fields reported, nothing saved); `test_patient_pages.py::test_invalid_registration_keeps_the_values_and_identifies_each_field` (summary linked to the fields, message next to each field) |
| Given an authenticated doctor, when they attempt to register a patient, then the system refuses the action. | `test_us03_patient_registration.py::test_doctors_are_refused_by_the_api` (HTTP 403), `::test_doctors_are_refused_by_the_registration_page` (GET and POST, HTTP 403 "Access denied"), `::test_doctors_cannot_open_a_patient_record_through_the_registration_pages`; nothing is saved in any case; in a browser: `test_patient_registration.py::test_doctors_cannot_register_patients` (no Patients link, the form returns "Access denied" with HTTP 403) |

## Cases of T-03.4

| Case | Verified by |
| --- | --- |
| Persistence | `test_us03_patient_registration.py::test_valid_patient_is_saved_with_every_field`, `::test_only_name_and_date_of_birth_are_needed` (values trimmed, blank contacts stored as NULL); `test_patient.py` (required columns, blank-name check constraint, defaults, record number) |
| Missing required fields | `test_us03_patient_registration.py::test_missing_required_fields_are_rejected_and_identified`; `test_patient_rules.py::test_missing_name_and_date_of_birth_are_both_reported` |
| Invalid dates | `test_us03_patient_registration.py::test_invalid_dates_of_birth_are_rejected` (impossible day and month, wrong format, tomorrow, before 1900; API and page), `::test_a_patient_born_today_is_accepted`; `test_patient_rules.py::test_dates_that_are_not_real_iso_dates_are_rejected`, `::test_date_of_birth_limits` |
| Denied doctor access | criterion 3 above |
| Denied access without a valid session ([requirements.md](../requirements.md) §2.4) | `test_us03_patient_registration.py::test_requests_without_a_session_are_refused` (API HTTP 401, page HTTP 401 with the login page), `::test_a_deactivated_account_can_no_longer_register`; `test_us01_authentication.py` lists `POST /api/patients` among the routes that refuse requests without a CSRF token |

## Mutation checks

The tests were checked against deliberate faults in the application code, each of which made at least one test of `test_us03_patient_registration.py` fail: doctors allowed on the registration page; doctors allowed in the API; future dates of birth accepted; the page filling in a missing date of birth; the e-mail not stored; new patients created inactive. The end-to-end test fails when the confirmation is removed, when the record is rendered directly after the POST instead of a redirect (the reload then registers the patient twice), when the focus no longer moves to the invalid field and when the phone is missing from the record.
