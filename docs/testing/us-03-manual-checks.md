# US-03 manual checks

Manual test cases of T-03.6 (#36): field labels, validation messages and keyboard navigation of the patient registration form. They complement the automated tests in [us-03-automated-tests.md](us-03-automated-tests.md) with checks that need human judgement: whether labels and messages are clear, whether the focus is visible and whether the form can be used without a mouse.

## Run

| | |
| --- | --- |
| Date | 2026-11-18 |
| Tester | Cecília Galvão |
| Application version | `main` at `97de1e8` (after #35) |
| Browser and version | Google Chrome 157.0.8103.79 (official build, 64-bit, Stable) |
| Operating system | Windows 11 Pro 25H2, build 26200.9974 |
| Screen | 1920 × 1080 at 150 % scaling (1280 × 720 effective), one monitor |
| Test data | Seeded development accounts `dev.receptionist` and `dev.doctor`; one synthetic patient, "Teste Manual" |

Result values: **Pass**, or **Fail** with a link to the defect issue.

## Preparation

1. Start the stack and seed the accounts ([running-locally.md](../development/running-locally.md)):

   ```bash
   docker compose up -d --build
   docker compose run --rm app python -m app.seed
   ```

2. Open <http://localhost:8000/login> and log in as `dev.receptionist`. The password of the development accounts is `SEED_PASSWORD` from `.env`.
3. Open **Patients**, then **Register a patient**.

## A. Labels

| ID | Check | Steps | Expected result | Result |
| --- | --- | --- | --- | --- |
| A1 | Visible labels | Look at the form. | Four fields with a visible label: "Full name (required)", "Date of birth (required)", "Phone", "E-mail". | Pass |
| A2 | Labels linked to fields | Click the text of each label. | The focus moves to the field of that label. | Pass |
| A3 | Hints | Read the text under "Phone" and "E-mail". | Phone: "Optional. 8 to 15 digits, for example +55 11 91234-5678."; E-mail: "Optional." | Pass |
| A4 | No autofill of other people's data | Start typing a name, a phone and an e-mail. | The browser does not suggest saved names, phones or e-mails. | Pass |

## B. Validation messages

| ID | Check | Steps | Expected result | Result |
| --- | --- | --- | --- | --- |
| B1 | Error summary | Click "Register patient" with every field empty. | A red box at the top says "The patient was not registered. Check these fields:" and lists the name and the date of birth. | Pass |
| B2 | Messages at the fields | Look at the fields after B1. | A red message above "Full name" and above "Date of birth"; both fields have a red border. | Pass |
| B3 | Page title | Look at the browser tab after B1. | The title starts with "Error: Register a patient". | Pass |
| B4 | Summary links | Click the second item of the summary, "Enter the date of birth." | The focus moves to the date of birth field. | Pass |
| B5 | Several invalid fields | Name "Teste Manual", date of birth tomorrow, phone `12`, e-mail `abc`; submit. | Messages for the date ("cannot be in the future"), the phone ("8 to 15 digits") and the e-mail ("such as name@example.com"); the name stays filled in. | Pass |
| B6 | Wording | Read the messages of B1 to B5. | Each message says what is wrong and what to enter instead, without technical terms. | Pass |

## C. Keyboard navigation

Use only the keyboard: Tab, Shift+Tab and Enter.

| ID | Check | Steps | Expected result | Result |
| --- | --- | --- | --- | --- |
| C1 | Initial focus | Open the form. | The focus is already in "Full name", with a visible orange outline. | Pass |
| C2 | Tab order and visible focus | Press Tab repeatedly. | Full name → Date of birth → Phone → E-mail → "Register patient" → "Cancel"; every element shows the outline when focused. | Pass — in Chrome, Tab also stops at the month, day, year and calendar button of the date field before moving to Phone; this is the browser's native date field |
| C3 | Date with the keyboard | Type the date of birth with the keyboard. | The date can be filled in without the mouse. | Pass |
| C4 | Submit with Enter, error | Leave the name empty, fill in the rest and press Enter. | The form is submitted and returns with the error; the focus is in "Full name". | Pass |
| C5 | Submit with Enter, success | Fill in the name "Teste Manual" and press Enter. | The record opens with the blue banner "Patient registered with record number P-…". | Pass |
| C6 | Links on the record | Press Tab on the record. | "Register another patient" and "Back to patients" are reached and open with Enter. | Pass |
| C7 | Skip link | Press Tab once at the top of a page. | "Skip to content" appears; Enter skips the navigation. | Pass |

## D. Record and access

| ID | Check | Steps | Expected result | Result |
| --- | --- | --- | --- | --- |
| D1 | Reload after saving | On the record of C5, press F5. | The record reloads with the same record number, and no second patient is created. | Pass — the database holds one "Teste Manual" |
| D2 | Doctor | Log out, log in as `dev.doctor` and open <http://localhost:8000/patients/new>. | No "Patients" link in the navigation; the page shows "Access denied". | Pass |

## Summary

19 of 19 checks pass; no defect was found.

- The keyboard checks were repeated in headless Chromium against the same version, with the same result: the labels are linked to the four fields, the focus starts in "Full name", the Tab order is the one of C2 (including the segments of the date field), Enter on the empty form returns the error page with the focus in "Full name", the invalid field carries `aria-invalid` and `aria-describedby`, and the first Tab of a page reaches "Skip to content".
- The Windows edition, build, resolution and scaling were read from the tester's machine.
