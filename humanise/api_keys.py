import json
import time
import secrets
import threading
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict

KEYS_FILE = Path(__file__).parent / "keys.json"
_lock = threading.Lock()

FREE_DAILY_LIMIT = 50
FREE_MINUTE_LIMIT = 5

PARTNER_DOMAINS = [
    "aifreelancewriter.workers.dev",
    "ai-freelance-writer.aifreelancewriter.workers.dev",
    "humanise.pages.dev",
    "humanise.onrender.com",
]


@dataclass
class ApiKey:
    key: str
    tier: str = "free"
    created_at: float = 0.0
    total_requests: int = 0
    daily_requests: int = 0
    daily_reset: float = 0.0
    minute_requests: int = 0
    minute_reset: float = 0.0
    name: str = ""


_keys: dict[str, ApiKey] = {}


def _load():
    global _keys
    if KEYS_FILE.exists():
        data = json.loads(KEYS_FILE.read_text())
        _keys = {k: ApiKey(**v) for k, v in data.items()}
    else:
        _keys = {}


def _save():
    KEYS_FILE.write_text(json.dumps({k: asdict(v) for k, v in _keys.items()}, indent=2))


def init():
    with _lock:
        _load()


def generate_key(name: str = "", tier: str = "free") -> ApiKey:
    with _lock:
        _load()
        key = f"hu_{secrets.token_hex(16)}"
        api_key = ApiKey(
            key=key,
            tier=tier,
            created_at=time.time(),
            name=name,
        )
        _keys[key] = api_key
        _save()
        return api_key


def validate_key(key: str) -> Optional[ApiKey]:
    with _lock:
        _load()
    return _keys.get(key)


def check_rate_limit(key: str, origin: str = "") -> dict:
    now = time.time()
    with _lock:
        _load()
        api_key = _keys.get(key)
        if not api_key:
            return {"allowed": False, "error": "invalid_key", "message": "Invalid API key"}

        if api_key.tier in ("paid", "partner"):
            return {"allowed": True, "tier": api_key.tier, "remaining": -1}

        for domain in PARTNER_DOMAINS:
            if domain in origin:
                return {"allowed": True, "tier": "partner", "remaining": -1}

        if now - api_key.daily_reset > 86400:
            api_key.daily_requests = 0
            api_key.daily_reset = now

        if now - api_key.minute_reset > 60:
            api_key.minute_requests = 0
            api_key.minute_reset = now

        if api_key.daily_requests >= FREE_DAILY_LIMIT:
            reset_in = int(86400 - (now - api_key.daily_reset))
            _save()
            return {
                "allowed": False,
                "error": "rate_limit_exceeded",
                "message": f"Free tier: {FREE_DAILY_LIMIT} requests/day. Upgrade at humanise.pages.dev/upgrade",
                "retry_after": reset_in,
                "limit": FREE_DAILY_LIMIT,
                "remaining": 0,
                "reset": int(api_key.daily_reset + 86400),
            }

        if api_key.minute_requests >= FREE_MINUTE_LIMIT:
            reset_in = int(60 - (now - api_key.minute_reset))
            _save()
            return {
                "allowed": False,
                "error": "rate_limit_exceeded",
                "message": f"Free tier: {FREE_MINUTE_LIMIT} requests/minute. Please slow down.",
                "retry_after": reset_in,
                "limit": FREE_MINUTE_LIMIT,
                "remaining": 0,
                "reset": int(api_key.minute_reset + 60),
            }

        api_key.daily_requests += 1
        api_key.minute_requests += 1
        api_key.total_requests += 1
        _save()

        return {
            "allowed": True,
            "tier": "free",
            "limit": FREE_DAILY_LIMIT,
            "remaining": FREE_DAILY_LIMIT - api_key.daily_requests,
            "reset": int(api_key.daily_reset + 86400),
        }


def get_usage(key: str) -> Optional[dict]:
    with _lock:
        _load()
    api_key = _keys.get(key)
    if not api_key:
        return None
    now = time.time()
    if now - api_key.daily_reset > 86400:
        api_key.daily_requests = 0
    return {
        "key": api_key.key[:8] + "...",
        "tier": api_key.tier,
        "name": api_key.name,
        "total_requests": api_key.total_requests,
        "daily_requests": api_key.daily_requests,
        "daily_limit": FREE_DAILY_LIMIT if api_key.tier == "free" else None,
        "daily_reset": int(api_key.daily_reset + 86400) if api_key.tier == "free" else None,
    }
