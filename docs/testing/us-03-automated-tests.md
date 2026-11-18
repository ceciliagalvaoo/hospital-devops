# US-03 automated tests

This document maps each acceptance criterion of US-03, register a patient ([backlog.md](../backlog.md) §3), and each case of T-03.4 (#34) to the automated tests that verify it. All tests use synthetic accounts and synthetic patients (`Synthetic Patient`, `example.test` addresses), never real patient information. They run in the `Tests` job of CI on every pull request.

Run them locally against the test database ([testing.md](../development/testing.md)):

```bash
pytest tests/test_patient_rules.py tests/integration/test_patient.py tests/integration/test_patient_api.py tests/integration/test_patient_pages.py tests/integration/test_us03_patient_registration.py
```

## Test modules

| Module | Tests | Scope |
| --- | --- | --- |
| `tests/integration/test_patient.py` | 8 | patient model, migration and database constraints (T-03.1, #31) |
| `tests/test_patient_rules.py` | 29 | registration rules: required fields, length, dates, phone and e-mail formats (T-03.2, #32) |
| `tests/integration/test_patient_api.py` | 5 | `POST /api/patients` (T-03.2, #32) |
| `tests/integration/test_patient_pages.py` | 10 | registration form and record page: labels, error summary, values kept, focus (T-03.3, #33) |
| `tests/integration/test_us03_patient_registration.py` | 36 | acceptance and access cases of T-03.4 (#34), each through the API and the page |

## Acceptance criteria

| US-03 acceptance criterion | Verified by |
| --- | --- |
| Given an authenticated receptionist and valid patient information, when registration is submitted, then the patient is saved and can be found through patient search. | Saved: `test_us03_patient_registration.py::test_valid_patient_is_saved_with_every_field` (receptionist and administrator, API and page, every field read back from the database), `::test_only_name_and_date_of_birth_are_needed`, `::test_each_registration_gets_its_own_record_number`, `::test_saved_patient_is_shown_on_its_record`. Found through search: verified when US-09 is integrated (T-09.3, #40, and T-09.4, #41), as the story's note states. |
| Given a missing required name or date of birth, when registration is submitted, then the system rejects it and identifies the missing fields. | `test_us03_patient_registration.py::test_missing_required_fields_are_rejected_and_identified` (name, blank name, date of birth and both; API and page; HTTP 422, exactly the missing fields reported, nothing saved); `test_patient_pages.py::test_invalid_registration_keeps_the_values_and_identifies_each_field` (summary linked to the fields, message next to each field) |
| Given an authenticated doctor, when they attempt to register a patient, then the system refuses the action. | `test_us03_patient_registration.py::test_doctors_are_refused_by_the_api` (HTTP 403), `::test_doctors_are_refused_by_the_registration_page` (GET and POST, HTTP 403 "Access denied"), `::test_doctors_cannot_open_a_patient_record_through_the_registration_pages`; nothing is saved in any case |

## Cases of T-03.4

| Case | Verified by |
| --- | --- |
| Persistence | `test_us03_patient_registration.py::test_valid_patient_is_saved_with_every_field`, `::test_only_name_and_date_of_birth_are_needed` (values trimmed, blank contacts stored as NULL); `test_patient.py` (required columns, blank-name check constraint, defaults, record number) |
| Missing required fields | `test_us03_patient_registration.py::test_missing_required_fields_are_rejected_and_identified`; `test_patient_rules.py::test_missing_name_and_date_of_birth_are_both_reported` |
| Invalid dates | `test_us03_patient_registration.py::test_invalid_dates_of_birth_are_rejected` (impossible day and month, wrong format, tomorrow, before 1900; API and page), `::test_a_patient_born_today_is_accepted`; `test_patient_rules.py::test_dates_that_are_not_real_iso_dates_are_rejected`, `::test_date_of_birth_limits` |
| Denied doctor access | criterion 3 above |
| Denied access without a valid session ([requirements.md](../requirements.md) §2.4) | `test_us03_patient_registration.py::test_requests_without_a_session_are_refused` (API HTTP 401, page HTTP 401 with the login page), `::test_a_deactivated_account_can_no_longer_register`; `test_us01_authentication.py` lists `POST /api/patients` among the routes that refuse requests without a CSRF token |

## Mutation checks

The tests were checked against deliberate faults in the application code, each of which made at least one test of `test_us03_patient_registration.py` fail: doctors allowed on the registration page; doctors allowed in the API; future dates of birth accepted; the page filling in a missing date of birth; the e-mail not stored; new patients created inactive.
