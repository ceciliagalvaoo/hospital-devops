# Accounts, sessions and access control

**Staff accounts** have a unique login, one of the roles `receptionist`, `doctor` or `administrator` (enforced by a database check constraint) and an active flag. Passwords are stored only as bcrypt hashes with a cost factor of 12 (NFR-03 requires at least 10). bcrypt uses at most 72 bytes of a password, so longer passwords are rejected instead of being silently truncated. Logins are stored in lower case and compared in lower case at login, so `Dev.Doctor` and `dev.doctor` are the same account (decided in the Sprint 2 planning after the Sprint 1 review); a login has 3 to 64 letters, digits, dots, hyphens or underscores and starts with a letter or a digit. Administrators create accounts with `POST /api/staff` (US-14); a new password needs at least 12 characters.

**Log in and out** through the authentication endpoints:

| Endpoint | Behaviour |
| --- | --- |
| `POST /auth/login` | Form fields `login` and `password`. Valid credentials of an active account return the login and role and set the session cookie. Wrong passwords, unknown logins and inactive accounts receive HTTP 401 with the same message. |
| `POST /auth/logout` | Deletes the session and clears the cookie (HTTP 204). |
| `GET /auth/me` | Returns the logged-in account, or HTTP 401 without a valid session. |
| `GET /auth/csrf` | Returns the CSRF token for the next state-changing request (`{"csrf_token": "..."}`) and sets the pre-session cookie when the browser has no cookie yet. |

`POST /auth/login` and `POST /auth/logout` require a CSRF token (see below). With `curl`, fetch the token first and fetch it again after logging in, because the token changes with the session:

```bash
URL=http://127.0.0.1:8000
token() { curl -s -b cookies.txt -c cookies.txt "$URL/auth/csrf" | python3 -c 'import json, sys; print(json.load(sys.stdin)["csrf_token"])'; }

curl -b cookies.txt -c cookies.txt -H "X-CSRF-Token: $(token)" -d login=dev.doctor -d password=change-me-dev "$URL/auth/login"
curl -b cookies.txt "$URL/auth/me"
curl -b cookies.txt -c cookies.txt -H "X-CSRF-Token: $(token)" -X POST "$URL/auth/logout"
```

Sessions are stored server-side in the `staff_sessions` table, so logout and account deactivation take effect immediately. The cookie `hospital_session` holds a random token; the database keeps only its SHA-256 hash. The cookie is `HttpOnly` and `SameSite=Lax`, expires after eight hours and is marked `Secure` when `SESSION_COOKIE_SECURE=true`, which must be set whenever the application is served over HTTPS. Each login issues a new token and replaces the browser's previous session. Expired sessions and sessions of deactivated accounts are rejected and deleted. Every response except the static files is sent with `Cache-Control: no-store`, so the browser keeps no copy of a page with account data: after logging out, the Back button shows the login page instead of the previous page (#222).

**Protect a route** by declaring its access requirement with the dependencies in `app/access.py`, never by checking the session inside the route ([requirements.md](../requirements.md) §2.4):

```python
from typing import Annotated

from fastapi import Depends

from app.access import CurrentAccount, require_roles
from app.models import Role, StaffAccount

AdministratorAccount = Annotated[StaffAccount, Depends(require_roles(Role.ADMINISTRATOR))]


@router.get("/profile")
def profile(account: CurrentAccount): ...  # any logged-in role


@router.get("/accounts")
def list_accounts(account: AdministratorAccount): ...  # administrators only
```

| Request | Response |
| --- | --- |
| No session cookie, an unknown or expired session, or a deactivated account | HTTP 401 `Not authenticated.` |
| Valid session, but the account has none of the roles passed to `require_roles` | HTTP 403 `Not permitted for this role.` |

Authentication is always checked first, so a request without a valid session receives HTTP 401 even on a role-restricted route. `require_roles` accepts several roles (for example `require_roles(Role.RECEPTIONIST, Role.ADMINISTRATOR)`); the allowed roles of each route follow the RBAC matrix in [requirements.md](../requirements.md) §2.2. Checks that depend on the record, such as a doctor's own appointments or patients, belong to the route of the story that introduces the record.

**CSRF protection** applies to every state-changing request (`POST`, `PUT`, `PATCH`, `DELETE`) of the application, through an application-wide dependency in `app/csrf.py`; new routes are protected without extra code. Safe methods (`GET`, `HEAD`, `OPTIONS`) are not checked, so they must never change state.

| Request | Response |
| --- | --- |
| No CSRF token, a wrong token, or a token issued for another session or before login | HTTP 403 `CSRF token missing or invalid.` |
| `Origin` header of another site (or `null`), or `Sec-Fetch-Site: cross-site` | HTTP 403 `Cross-origin request refused.`, even with a valid token |

The token is an HMAC of the request's session cookie, or of the random pre-session cookie `hospital_csrf` before login, so the login form is protected too. Clients send it in the form field `csrf_token` (server-rendered forms) or the `X-CSRF-Token` header. Because each login issues a new session, it also issues a new CSRF token. The HMAC key is generated when the process starts, so no secret needs to be configured; a restart only invalidates forms that were open at that moment. The `hospital_csrf` cookie has the same `HttpOnly`, `SameSite=Lax` and `Secure` settings as the session cookie.
