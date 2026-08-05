"""Shared helper: refresh access token + call base.welast.vn via curl."""
import json, subprocess, os, time, random

REFRESH_TOKEN = os.environ.get("WELAST_REFRESH_TOKEN")  # no committed default; rotate + set in env
BASE = "https://base.welast.vn"

# Randomized pause between LIVE Facebook-proxied calls (see call_live). A fixed
# interval is itself a detectable robot pattern, so each waits a random amount in
# [LIVE_MIN, LIVE_MAX] seconds to look like a human clicking around a dashboard.
LIVE_MIN = float(os.environ.get("WELAST_LIVE_MIN", "2.0"))
LIVE_MAX = float(os.environ.get("WELAST_LIVE_MAX", "5.0"))
_LIVE_LAST = 0.0


def _is_live_path(path):
    """A WeLast path that proxies straight to the live Facebook Graph API."""
    return "/live" in path or path.lstrip("/").startswith("facebook/")

def get_token():
    cmd = ["curl", "-s", "-X", "POST", f"{BASE}/auth/refresh-token",
           "-H", "accept: application/json", "-H", "content-type: application/json",
           "-H", "origin: https://data.welast.vn",
           "-H", f"cookie: refreshToken={REFRESH_TOKEN}",
           "--data", json.dumps({"refreshToken": REFRESH_TOKEN})]
    out = subprocess.check_output(cmd, timeout=60).decode().strip()
    if out.startswith('"'):
        return json.loads(out)
    elif out.startswith("{"):
        d = json.loads(out)
        token = d.get("accessToken") or d.get("token") or d.get("access_token")
        if not token:
            raise Exception(f"Failed to get token, WeLast API returned: {out}")
        return token
    raise Exception(f"Unexpected token response: {out}")

def get(path, token):
    if not token:
        raise Exception("Cannot fetch from WeLast API: No access token provided.")
    if _is_live_path(path):
        raise RuntimeError(
            f"{path!r} is a LIVE Facebook-proxied endpoint. Reading it hammers the FB "
            "Graph API through WeLast's app token and can get the app flagged. Use "
            "call_live() (which throttles + requires WELAST_ALLOW_LIVE=1), not get().")
    cmd = ["curl", "-s", f"{BASE}{path}",
           "-H", "accept: application/json", "-H", "origin: https://data.welast.vn",
           "-H", f"authorization: Bearer {token}"]
    out = subprocess.check_output(cmd, timeout=90).decode().strip()
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        raise Exception(f"WeLast API returned non-JSON response: {out[:100]}...")


def call_live(path, token):
    """Call a LIVE Facebook-proxied WeLast endpoint (e.g. /facebook/.../live).

    WeLast does not store breakdowns server-side — these proxy to the Facebook
    Graph API via WeLast's app token, so a burst can get that app flagged. Guarded:
    refuses unless WELAST_ALLOW_LIVE=1, and spaces calls by a random pause. Intended
    for a deliberate, throttled, one-time backfill into our own data. Returns parsed
    JSON (usually a list) or None on error.
    """
    if not token:
        raise Exception("Cannot fetch from WeLast API: No access token provided.")
    if os.environ.get("WELAST_ALLOW_LIVE") != "1":
        raise RuntimeError(
            f"Refusing LIVE call to {path!r}: this proxies to the Facebook Graph API "
            "and can get WeLast's app flagged. Set WELAST_ALLOW_LIVE=1 only for a "
            "deliberate, throttled backfill into our own DB.")
    global _LIVE_LAST
    lo, hi = min(LIVE_MIN, LIVE_MAX), max(LIVE_MIN, LIVE_MAX)
    wait = random.uniform(lo, hi) - (time.monotonic() - _LIVE_LAST)
    if wait > 0:
        time.sleep(wait)
    _LIVE_LAST = time.monotonic()
    out = subprocess.run(
        ["curl", "-s", "--max-time", "70", "--retry", "3", "--retry-delay", "2",
         f"{BASE}{path}", "-H", "accept: application/json",
         "-H", "origin: https://data.welast.vn", "-H", f"authorization: Bearer {token}"],
        capture_output=True, text=True).stdout
    try:
        j = json.loads(out)
        return j if isinstance(j, list) else None
    except Exception:
        return None
