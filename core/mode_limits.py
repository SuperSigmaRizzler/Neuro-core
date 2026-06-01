import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from config import DATA_DIR
except Exception:
    DATA_DIR = "data"


LIMIT_FILE = Path(DATA_DIR) / "mode_limits.json"


MODE_LIMITS = {
    "pro": {
        "daily": 3,
        "label": "Pro",
        "message": "You've reached your limit for Pro mode today.",
        "subtitle": "Come back again tomorrow to use Pro mode again."
    },
    "god": {
        "daily": 1,
        "label": "GOD",
        "message": "You've reached your limit for GOD mode today.",
        "subtitle": "Come back again tomorrow to use GOD mode again."
    }
}


class ModeLimitError(Exception):
    def __init__(self, mode: str, limit: int, used: int):
        info = MODE_LIMITS.get(mode, MODE_LIMITS["pro"])
        self.mode = mode
        self.limit = limit
        self.used = used
        self.message = info["message"]
        self.subtitle = info["subtitle"]
        super().__init__(self.message)


def _today_key() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _load() -> dict:
    LIMIT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not LIMIT_FILE.exists():
        return {}

    try:
        return json.loads(LIMIT_FILE.read_text())
    except Exception:
        return {}


def _save(data: dict):
    LIMIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    LIMIT_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()


def build_limit_fingerprint(request, user=None, client_fp: str = "") -> str:
    """
    Server-side anti-bypass fingerprint.

    It stores only a hash, not raw IP/device/location.
    This is not perfect against VPN/incognito/new device,
    but much harder than frontend-only limits.
    """
    ip = (
        request.headers.get("CF-Connecting-IP")
        or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.remote_addr
        or "unknown-ip"
    )

    ua = request.headers.get("User-Agent", "unknown-agent")
    lang = request.headers.get("Accept-Language", "unknown-lang")

    user_part = ""
    if user and isinstance(user, dict):
        user_part = str(user.get("id") or user.get("username") or "")

    raw = "|".join([
        "neuromv-mode-limit-v1",
        str(user_part),
        str(ip),
        str(ua),
        str(lang),
        str(client_fp or "")
    ])

    return _sha(raw)


def mode_status(mode: str, fingerprint: str) -> dict:
    mode = str(mode or "").lower().strip()

    if mode not in MODE_LIMITS:
        return {
            "limited": False,
            "mode": mode,
            "used": 0,
            "limit": None,
            "remaining": None
        }

    data = _load()
    today = _today_key()
    limit = MODE_LIMITS[mode]["daily"]

    key = f"{today}:{mode}:{fingerprint}"
    used = int(data.get(key, {}).get("used", 0))
    remaining = max(0, limit - used)

    return {
        "limited": used >= limit,
        "mode": mode,
        "used": used,
        "limit": limit,
        "remaining": remaining,
        "message": MODE_LIMITS[mode]["message"],
        "subtitle": MODE_LIMITS[mode]["subtitle"]
    }


def check_mode_limit(mode: str, fingerprint: str):
    status = mode_status(mode, fingerprint)

    if status.get("limited"):
        raise ModeLimitError(
            mode=mode,
            limit=status["limit"],
            used=status["used"]
        )

    return status


def consume_mode_limit(mode: str, fingerprint: str):
    mode = str(mode or "").lower().strip()

    if mode not in MODE_LIMITS:
        return mode_status(mode, fingerprint)

    check_mode_limit(mode, fingerprint)

    data = _load()
    today = _today_key()
    key = f"{today}:{mode}:{fingerprint}"

    row = data.get(key, {
        "used": 0,
        "created_at": int(time.time())
    })

    row["used"] = int(row.get("used", 0)) + 1
    row["updated_at"] = int(time.time())
    data[key] = row

    _save(data)

    return mode_status(mode, fingerprint)
