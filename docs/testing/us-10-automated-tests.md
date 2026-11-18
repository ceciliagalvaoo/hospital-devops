# US-10 automated tests

This document maps each acceptance criterion of US-10, edit patient contact details ([backlog.md](../backlog.md) §3), and each case of T-10.3 (#45) to the automated tests that verify it. All tests use synthetic accounts and synthetic patients, never real patient information. They run in the `Tests` job of CI on every pull request.

Run them locally against the test database ([testing.md](../development/testing.md)):

```bash
pytest tests/test_patient_rules.py tests/integration/test_patient_contacts.py tests/integration/test_patient_contacts_page.py tests/integration/test_us10_contact_update.py
```

## Test modules

| Module | Tests | Scope |
| --- | --- | --- |
| `tests/test_patient_rules.py` | 5 of its tests | contact rules: trimming, removal of an empty contact, all errors reported, the same phone rule as registration (T-10.1, #43) |
| `tests/integration/test_patient_contacts.py` | 7 | `POST /api/patients/<id>/contacts` (T-10.1, #43) |
| `tests/integration/test_patient_contacts_page.py` | 9 | the contact-edit form and the save confirmation: current values, error summary, values kept, focus (T-10.2, #44) |
| `tests/integration/test_us10_contact_update.py` | 28 | acceptance and access cases of T-10.3 (#45), each through the API and the page |
| `tests/integration/test_us01_authentication.py` | (shared) | both contact routes refuse requests without a CSRF token |

## Acceptance criteria

| US-10 acceptance criterion | Verified by |
| --- | --- |
| Given a receptionist or administrator and valid contact details, when the changes are saved, then the updated details are persisted and displayed after reloading the record. | `test_us10_contact_update.py::test_valid_contacts_are_saved_and_shown_after_reloading_the_record` (receptionist and administrator, API and page; the database holds the new phone and e-mail, name and date of birth are unchanged, and the reloaded record shows the new values), `::test_one_contact_can_change_and_an_empty_one_is_removed`, `::test_values_are_trimmed`; `test_patient_contacts_page.py::test_saving_shows_the_record_with_a_confirmation` |
| Given invalid contact details, when the changes are submitted, then the system rejects them and identifies the invalid fields. | `test_us10_contact_update.py::test_invalid_contacts_are_rejected_identified_and_change_nothing` (short and long phone numbers, letters, an e-mail without a domain or with a space, both invalid; API and page; HTTP 422, exactly the invalid fields reported, the record unchanged and shown unchanged); `test_patient_contacts_page.py::test_invalid_contacts_keep_the_values_identify_the_fields_and_change_nothing` (summary, field messages, focus) |
| Given an authenticated doctor, when they attempt to edit patient contact details, then the system refuses the action. | `test_us10_contact_update.py::test_doctors_are_refused_by_the_api` (HTTP 403), `::test_doctors_are_refused_by_the_contact_form` (GET and POST, HTTP 403 "Access denied", the current contacts not shown); nothing is changed in any case |

## Cases of T-10.3

| Case | Verified by |
| --- | --- |
| Valid updates | criterion 1 above |
| Invalid updates | criterion 2 above; `test_patient_rules.py::test_invalid_contacts_are_all_reported`, `::test_registration_and_contact_updates_apply_the_same_phone_rule` |
| Persistence | every test of `test_us10_contact_update.py` reads the stored values back from the database after expiring the session, and the valid cases also reload the record page |
| Denied doctor access | criterion 3 above |
| Denied access without a valid session ([requirements.md](../requirements.md) §2.4) | `test_us10_contact_update.py::test_updates_without_a_session_are_refused` (API HTTP 401, page HTTP 401 with the login page), `::test_a_deactivated_account_can_no_longer_update` |
| Unknown patient | `test_us10_contact_update.py::test_unknown_patients_are_not_found` (HTTP 404 through the API and the page) |

## Mutation checks

Each of these faults in the application code made tests of `test_us10_contact_update.py` fail: doctors allowed in the API; doctors allowed to submit the form; the page saving the submitted values before validating them; an empty e-mail keeping the old one; contact updates skipping the e-mail rule.
