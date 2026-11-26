# US-02 manual checks

Manual test cases of T-02.6 (#60): the labels of the doctor registration form, in particular the availability inputs, and the wording of its validation messages, with keyboard use and the result of a registration. They complement the automated tests in [us-02-automated-tests.md](us-02-automated-tests.md) with checks that need human judgement: whether labels and messages are clear and whether the form can be used without a mouse.

## Run

| | |
| --- | --- |
| Date | 2026-11-26 |
| Tester | Cecília Galvão |
| Application version | `main` at `e9584b1` (after #59) |
| Browser and version | Google Chrome 158.0.8127.38 |
| Operating system | Windows 11 Pro 25H2, build 26200.9974 |
| Screen | 1920 × 1080 at 150 % scaling (1280 × 720 effective), one monitor |
| Test data | Seeded development accounts `dev.administrator`, `dev.doctor` (the only doctor account without a profile) and `dev.receptionist`; synthetic doctor names |

Result values: **Pass**, or **Fail** with a link to the defect issue. Because `dev.doctor` was the only doctor account available, every submission except C4 was invalid and saved nothing; B2 to B6 were run after C4, when the account was already linked, so their summaries also listed the missing staff account, as expected.

## Preparation

1. Start the stack and seed the accounts ([running-locally.md](../development/running-locally.md)):

   ```bash
   docker compose up -d --build
   docker compose run --rm app python -m app.seed
   ```

2. Open <http://localhost:8000/login> and log in as `dev.administrator`. The password of the development accounts is `SEED_PASSWORD` from `.env`.
3. Open **Doctors**, then **Register a doctor**.

## A. Labels

| ID | Check | Steps | Expected result | Result |
| --- | --- | --- | --- | --- |
| A1 | Labels of the details | Look at the top of the form. | "Staff account (required)" with the hint "Active doctor accounts without a doctor profile.", "Full name (required)", "Specialisation (required)". | Pass |
| A2 | Account choices | Open the staff account list. | "Choose a doctor account…" and `dev.doctor`. | Pass |
| A3 | Specialisation choices | Open the specialisation list. | The eight readable names, from "General practice" to "Psychiatry". | Pass |
| A4 | Availability group | Look at "Weekly availability (required)". | A hint about at least one range, the half hour, no overlap and leaving unused rows empty, followed by Range 1 to Range 6. | Pass |
| A5 | Row labels | Look at each range. | "Weekday", "Start" and "End"; the weekday list shows Monday to Sunday with whole names ("Wednesday" not cut). | Pass |
| A6 | Labels linked to fields | Click the text "Start" of Range 1. | The focus moves to the start field of that row. | Pass |

## B. Validation wording

| ID | Check | Steps | Expected result | Result |
| --- | --- | --- | --- | --- |
| B1 | Empty form | Submit the empty form. | A red summary lists the account, the name, the specialisation and "Add at least one weekly availability range."; the page title starts with "Error:". | Pass |
| B2 | Incomplete range | Range 1: Monday, 08:00, no end. | At Range 1: "Choose the weekday and enter the start and end of this range."; the other fields keep their values. | Pass |
| B3 | Time off the half hour | Range 1: Monday 08:15–12:00. | "Enter the times on the half hour, as HH:MM, for example 08:00 or 13:30." | Pass |
| B4 | End before start | Range 1: Monday 12:00–08:00. | "The end of this range must be after its start." | Pass |
| B5 | Overlap | Range 1: Monday 08:00–12:00; Range 2: Monday 11:00–13:00. | At Range 2 only: "This range overlaps another range on the same day."; Range 1 without an error. | Pass |
| B6 | Summary link to a row | In the result of B5, click the overlap item of the summary. | The focus moves to the weekday of Range 2. | Pass |
| B7 | Wording | Read the messages of B1 to B5. | Each message says what is wrong and what to enter instead, without technical terms. | Pass |

## C. Keyboard and a valid registration

| ID | Check | Steps | Expected result | Result |
| --- | --- | --- | --- | --- |
| C1 | Initial focus and Tab order | Reload the form and press Tab repeatedly. | The focus starts in "Staff account"; then name, specialisation, Range 1 (weekday, start, end), Range 2 …, "Register doctor", "Cancel"; every element shows the orange outline. | Pass — Chrome also stops inside each time field (hours, minutes, AM/PM, clock button); this is the browser's native time field |
| C2 | Weekday with the keyboard | In a weekday list, use the arrow keys or type "M". | A weekday can be chosen without the mouse. | Pass |
| C3 | Time with the keyboard | Type a start time with the keyboard. | The time can be filled in without the mouse. | Pass |
| C4 | Valid registration with Enter | `dev.doctor`, "Dr Teste Manual", Cardiology; Monday 08:00–12:00, Monday 12:00–14:00, Thursday 13:30–17:00; press Enter. | The profile opens with "Doctor registered and linked to the account dev.doctor." and the three ranges in order. | Pass — Thursday was entered as 11:30–17:00; the profile and the database hold Monday 08:00–12:00, Monday 12:00–14:00 (adjacent, accepted) and Thursday 11:30–17:00 |
| C5 | List and account offered | "Back to doctors", then "Register a doctor". | The doctor is listed; `dev.doctor` is no longer offered and the notice says that every doctor account has a profile. | Pass |

## D. Access

| ID | Check | Steps | Expected result | Result |
| --- | --- | --- | --- | --- |
| D1 | Receptionist | Log in as `dev.receptionist` and open <http://localhost:8000/doctors/new>. | No "Doctors" link in the navigation; the page shows "Access denied". | Pass |

## Summary

19 of 19 checks pass; no defect was found.

- The application's request log of the run confirms the submissions: six rejected registrations (HTTP 422, B1 to B5 and one more invalid attempt), one accepted registration (HTTP 303, C4) followed by the profile, the list and the form (C5), and HTTP 403 for the receptionist (D1); the database held one doctor afterwards. C4 and B2 to B5 were run in a second pass, after the log showed that they had not been submitted yet; only checks confirmed by the run are recorded as passed.
- The label and keyboard checks were repeated in headless Chromium against the same version, with the same result: every control has a label, the focus starts in "Staff account", the Tab order is the one of C1, the overlap is reported at Range 2 only, the page title starts with "Error:" and the summary link moves the focus to the weekday of Range 2.
- The browser version, the Windows edition, build, resolution and scaling were read from the tester's machine.
