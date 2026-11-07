# US-01 manual checks

Manual test cases of T-01.8 (#12): login messages, keyboard navigation and the layout on a small screen. They complement the automated tests in [us-01-automated-tests.md](us-01-automated-tests.md) with checks that need human judgement: whether messages are clear, whether the focus is visible and whether the layout is usable.

## Run

| | |
| --- | --- |
| Date | 2026-11-07 |
| Tester | Cecília Galvão |
| Application version | `main` at `5603992` (after the fix of defect #202) |
| Browser and version | Google Chrome 156.0.8078.80 |
| Operating system | Windows 11 Pro, build 26200 |
| Screen | 1920 × 1080 at 150 % scaling (1280 × 720 effective); small screens through Chrome's device emulation |
| Test data | Seeded development accounts `dev.receptionist`, `dev.doctor`, `dev.administrator` (synthetic) |

Result values: **Pass**, or **Fail** with a link to the defect issue.

## Preparation

1. Start the stack and seed the accounts (README §11):

   ```bash
   docker compose up -d --build
   docker compose run --rm app python -m app.seed
   ```

2. Open <http://127.0.0.1:8000/login>. The password of the development accounts is `SEED_PASSWORD` from `.env`.
3. Log out and close other tabs of the application between sections, so that each section starts without a session.

## A. Login messages

| ID | Check | Steps | Expected result | Result |
| --- | --- | --- | --- | --- |
| A1 | Wrong password | Log in as `dev.doctor` with a wrong password. | The message "Invalid login or password." appears above the form, in red; the login stays filled in and the password field is empty. | Pass |
| A2 | Unknown login | Log in as `dev.nobody` with any password. | Exactly the same message as in A1, so it does not reveal whether a login exists. | Pass |
| A3 | Inactive account | Deactivate `dev.doctor` (command below), log in with the correct password, then reactivate it. | Exactly the same message as in A1. | Pass |
| A4 | Empty fields | Click "Log in" with both fields empty, then with only the login filled in. | The browser asks to fill in the empty field and the form is not sent. | Pass — Chrome shows "Preencha este campo." (browser language) for the empty field |
| A5 | Page without a session | Open <http://127.0.0.1:8000/appointments> without being logged in. | The login page shows "Please log in to continue." | Pass |
| A6 | Area of another role | Log in as `dev.receptionist` and open <http://127.0.0.1:8000/staff>. | An "Access denied" page says "Your role does not have access to this page." and keeps the navigation and the logout button. | Pass |
| A7 | Expired form | Open the login page, restart the application (command below), then log in. | A page says "The form has expired. Go back, reload the page and try again."; after reloading the login page, login works. | Pass — message and recovery after reload as expected; see A8 for the page title |
| A8 | Wording | Read the messages of A1 to A7. | Each message is understandable without technical terms and says what to do next where needed. | **Fail** — the expired-form page (A7) is titled "Access denied", which contradicts its message: defect #204 |

Commands for A3 and A7, in the repository folder:

```bash
# A3: deactivate, then reactivate after the check
docker compose exec db psql -U hospital -d hospital -c "UPDATE staff_accounts SET is_active = false WHERE login = 'dev.doctor'"
docker compose exec db psql -U hospital -d hospital -c "UPDATE staff_accounts SET is_active = true WHERE login = 'dev.doctor'"

# A7: restart the application, which renews the CSRF key
docker compose restart app
```

## B. Keyboard navigation

Use only the keyboard: Tab, Shift+Tab, Enter and Space.

| ID | Check | Steps | Expected result | Result |
| --- | --- | --- | --- | --- |
| B1 | Login with the keyboard | Open the login page, type the login, Tab, type the password, Enter. | The focus starts in the Login field; Tab moves to Password and then to "Log in"; Enter logs in. | Pass |
| B2 | Visible focus | Move through the login page and the home page with Tab. | Every focused link, field and button has a clearly visible outline. | Pass |
| B3 | Skip link | On the home page, press Tab once, then Enter. | "Skip to content" appears at the top; Enter moves the focus to the page content, so the next Tab skips the header. | Pass |
| B4 | Navigation | On the home page of `dev.administrator`, Tab through the header and the cards, and open an area with Enter. | The order is skip link, title, navigation links, logout button, then the area cards; Enter opens the focused area. | Pass |
| B5 | Access denied page | On the "Access denied" page (A6), reach "Back to the home page" with Tab and press Enter. | The home page opens. | Pass |
| B6 | Logout with the keyboard | Tab to "Log out" and press Enter, then repeat with Space after logging in again. | Both log out and show the login page. | Pass |
| B7 | No keyboard trap | Tab forwards and Shift+Tab backwards through each page. | The focus never gets stuck in an element. | Pass |

## C. Small screen

Use the device emulation of the browser's developer tools (Chrome or Edge: F12, then Ctrl+Shift+M).

| ID | Check | Steps | Expected result | Result |
| --- | --- | --- | --- | --- |
| C1 | Login page at 320 px | Width 320 px: open the login page and trigger the error of A1. | No horizontal scrolling; fields and button use the full width; the message wraps inside the card. | Pass |
| C2 | Home pages at 320 px | Width 320 px: log in as each of the three accounts. | No horizontal scrolling; the header wraps without overlapping; the long heading of `dev.administrator` wraps (defect #202); the cards are stacked. | Pass |
| C3 | Access denied at 320 px | Width 320 px: repeat A6. | The page fits the screen and the navigation stays usable. | Pass |
| C4 | Mobile device size | Choose "iPhone SE" (375 × 667) and repeat C1 to C3 briefly. | Same as C1 to C3. | Pass |
| C5 | 200 % zoom | Without device emulation, zoom the desktop browser to 200 % (Ctrl and +) on the login and home pages. | All content is readable and usable without horizontal scrolling. | Pass |

## Summary

19 of 20 checks pass; 1 fails.

- **A8 fails:** an expired form is reported on a page titled "Access denied", although the message correctly says that the form has expired. The behaviour is otherwise correct (HTTP 403, login works after reloading). Recorded as defect #204 (T-01.11) and fixed in its own pull request.
- Before this run, a browser pre-check of the small-screen layout found defect #202 (horizontal scrolling of the administrator's home page at 320 px), which was fixed in `5603992`; C2 confirms the fix.
- Messages for wrong passwords, unknown logins and inactive accounts are identical (A1 to A3), so they do not reveal whether a login exists.
