# US-09 automated tests

This document maps each acceptance criterion of US-09, search for a patient ([backlog.md](../backlog.md) §3), and each case of T-09.3 (#40) to the automated tests that verify it. All tests use synthetic accounts and synthetic patients, never real patient information. The unit and integration tests run in the `Tests` job of CI on every pull request; the browser end-to-end tests (T-09.4, #41) run with `pytest -m e2e` in the `E2E` job.

Run them locally against the test database ([testing.md](../development/testing.md)):

```bash
pytest tests/test_patient_search_rules.py tests/integration/test_patient_search.py tests/integration/test_patient_search_page.py tests/integration/test_us09_patient_search.py
pytest -m e2e tests/e2e/test_search_and_open_patient.py   # browser end-to-end tests
```

## Test modules

| Module | Tests | Scope |
| --- | --- | --- |
| `tests/test_patient_search_rules.py` | 16 | reading a query: record-number forms, words of the name, empty and too short queries, literal wildcards (T-09.1, #38) |
| `tests/integration/test_patient_search.py` | 17 | search in the database and `GET /api/patients` (T-09.1, #38) |
| `tests/integration/test_patient_search_page.py` | 10 | the patients area page: form, result table, empty state, field message, escaping (T-09.2, #39) |
| `tests/integration/test_us09_patient_search.py` | 47 | acceptance and access cases of T-09.3 (#40), each through the API and the page |
| `tests/e2e/test_search_and_open_patient.py` | 3 | browser end-to-end: register two patients, search, open the correct record, empty state and query message, for receptionists and administrators; doctors refused (T-09.4, #41) |

## Acceptance criteria

| US-09 acceptance criterion | Verified by |
| --- | --- |
| Given an authenticated receptionist or administrator, when they search by patient name or identifier, then matching patients are listed. | `test_us09_patient_search.py::test_search_by_name_lists_exactly_the_matching_patients` (receptionist and administrator, API and page; part of a name, any case, several words), `::test_search_by_record_number_lists_that_patient` (`P-000042`, `P42`, `42`, `p-42`), `::test_inactive_patients_are_listed_too`, `::test_a_patient_registered_on_the_page_is_found_by_search`; in a browser: `test_search_and_open_patient.py::test_register_search_and_open_the_correct_record` (two patients registered through the form are both listed; the second name opens the second patient's record; several words and the record number find exactly one) |
| Given a search without matches, when it is submitted, then an empty-state message is displayed. | `test_us09_patient_search.py::test_search_without_matches_shows_the_empty_state` (an unknown name, an unknown record number and words that no single name contains; the page shows "No patients match …"); `test_patient_search_page.py::test_search_without_matches_shows_the_empty_state`; in a browser: the empty state of `test_search_and_open_patient.py::test_register_search_and_open_the_correct_record` |
| Given an authenticated doctor, when they attempt to use patient search, then the system refuses the action. | `test_us09_patient_search.py::test_doctors_are_refused` (API and page, with and without a query: HTTP 403, no patient listed); in a browser: `test_search_and_open_patient.py::test_doctors_cannot_search_patients` (no Patients link, "Access denied" and no search form) |

## Cases of T-09.3

| Case | Verified by |
| --- | --- |
| Matching results | criterion 1 above; results list exactly the matching patients, ordered by name |
| Empty queries | `test_us09_patient_search.py::test_empty_or_too_short_queries_show_a_message_instead_of_results` (empty, spaces only and one letter; HTTP 422, the message instead of a list); `test_patient_search_rules.py::test_empty_query_is_refused`, `::test_one_letter_is_too_short_but_one_digit_is_a_record_number` |
| No matches | criterion 2 above |
| Denied doctor access | criterion 3 above |
| Denied access without a valid session ([requirements.md](../requirements.md) §2.4) | `test_us09_patient_search.py::test_search_without_a_session_is_refused` (API HTTP 401, page HTTP 401 with the login page), `::test_a_deactivated_account_can_no_longer_search` |

## Mutation checks

Each of these faults in the application code made tests of `test_us09_patient_search.py` fail: doctors allowed in the API; doctors allowed on the page; any word of the query matching instead of every word; only the `P-000042` form accepted as a record number (exactly the `P42`, `42` and `p-42` cases failed, through both channels); inactive patients hidden; the empty-state message removed from the page.

The end-to-end test fails when every result row links to the first patient, when any word matches instead of every word, when record numbers are searched as names, when the empty state is removed and when the focus no longer moves to an unusable query. The first of these survived the first version of the test, which clicked a name only when one patient was listed; the test now opens the second of two listed patients.

## Known limitation

Search does not ignore accents: "Joao" does not find "João". Ignoring accents needs the PostgreSQL `unaccent` extension and is left as a later improvement ([running-locally.md](../development/running-locally.md)).
