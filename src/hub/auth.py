"""Private dashboard access: signed cookie + owner access code.

Telegram webhook stays public. Cloud Run fails closed if auth is not configured.
"""

from __future__ import annotations

import hmac
import os
import time
from hashlib import sha256
from urllib.parse import parse_qs

from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from hub.config import HUB_ACCESS_CODE, HUB_OWNER_EMAIL, HUB_REQUIRE_AUTH, HUB_SESSION_SECRET

COOKIE = "hub_session"
MAX_AGE = 60 * 60 * 24 * 30
_FAILS: dict[str, list[float]] = {}


def auth_enabled() -> bool:
    if HUB_REQUIRE_AUTH:
        return True
    return bool(HUB_ACCESS_CODE and HUB_SESSION_SECRET)


def auth_ready() -> bool:
    return bool(HUB_ACCESS_CODE and HUB_SESSION_SECRET)


def is_public_path(path: str) -> bool:
    if path in {"/health", "/login", "/auth/login", "/auth/logout", "/telegram/webhook"}:
        return True
    return path.startswith("/static/")


def _sign(payload: str) -> str:
    return hmac.new(HUB_SESSION_SECRET.encode(), payload.encode(), sha256).hexdigest()


def issue_cookie(response: Response, email: str) -> None:
    exp = int(time.time()) + MAX_AGE
    payload = f"v1|{email}|{exp}"
    token = f"{payload}|{_sign(payload)}"
    secure = os.getenv("K_SERVICE", "") != ""
    response.set_cookie(
        COOKIE,
        token,
        max_age=MAX_AGE,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
    )


def clear_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE, path="/")


def session_email(request: Request) -> str | None:
    raw = (request.cookies.get(COOKIE) or "").strip().strip('"')
    parts = raw.split("|")
    if len(parts) != 4 or parts[0] != "v1":
        return None
    version, email, exp_s, sig = parts
    payload = f"{version}|{email}|{exp_s}"
    if not hmac.compare_digest(sig, _sign(payload)):
        return None
    try:
        if int(exp_s) < int(time.time()):
            return None
    except ValueError:
        return None
    return email


def _client_key(request: Request) -> str:
    forwarded = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    return forwarded or (request.client.host if request.client else "unknown")


def too_many_failures(request: Request) -> bool:
    key = _client_key(request)
    now = time.time()
    hits = [t for t in _FAILS.get(key, []) if now - t < 900]
    _FAILS[key] = hits
    return len(hits) >= 8


def record_failure(request: Request) -> None:
    key = _client_key(request)
    _FAILS.setdefault(key, []).append(time.time())


def check_access_code(code: str) -> bool:
    expected = HUB_ACCESS_CODE.encode()
    given = (code or "").strip().encode()
    if not expected:
        return False
    if len(given) != len(expected):
        hmac.compare_digest(expected, expected)
        return False
    return hmac.compare_digest(given, expected)


async def read_login_code(request: Request) -> str:
    ctype = (request.headers.get("content-type") or "").lower()
    if "application/json" in ctype:
        body = await request.json()
        return str((body or {}).get("code") or "")
    raw = (await request.body()).decode("utf-8", errors="replace")
    return (parse_qs(raw).get("code") or [""])[0]


def login_redirect(email: str | None = None) -> RedirectResponse:
    response = RedirectResponse("/", status_code=303)
    issue_cookie(response, email or HUB_OWNER_EMAIL or "owner")
    return response
