"""Shared helper: refresh access token + call base.welast.vn via curl."""
import json, subprocess, os

DEFAULT_REFRESH_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6ImtoYW5obG1Ad2VsYXN0LnZuIiwiaXNBZG1pbiI6ZmFsc2UsInVzZXJuYW1lIjoibWFpX2xhbV9raGFuaCIsImlhdCI6MTc4NTEyMDkzMCwiZXhwIjoxNzg1NzI1NzMwfQ.hzzcDLyH3uynYsV4pqT7CjPZQDSzWTu7L5-_pLrjbi4"
REFRESH_TOKEN = os.environ.get("WELAST_REFRESH_TOKEN") or DEFAULT_REFRESH_TOKEN
BASE = "https://base.welast.vn"

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
    cmd = ["curl", "-s", f"{BASE}{path}",
           "-H", "accept: application/json", "-H", "origin: https://data.welast.vn",
           "-H", f"authorization: Bearer {token}"]
    out = subprocess.check_output(cmd, timeout=90).decode().strip()
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        raise Exception(f"WeLast API returned non-JSON response: {out[:100]}...")
