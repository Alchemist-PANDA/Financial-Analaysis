import os
import threading
import time
from typing import Any

_LOCK = threading.RLock()
CACHE: dict[str, dict[str, Any]] = {}


def _ttl_seconds() -> int:
    try:
        return int(os.getenv("ANALYSIS_CACHE_TTL_SECONDS", "30120"))
    except Exception:
        return 30120


def _stale_retention_seconds() -> int:
    try:
        return int(os.getenv("ANALYSIS_STALE_RETENTION_SECONDS", "604800"))
    except Exception:
        return 604800


def get_cached_entry(ticker: str) -> dict[str, Any] | None:
    normalized = (ticker or "").strip().upper()
    if not normalized:
        return None

    with _LOCK:
        entry = CACHE.get(normalized)
        if not entry:
            return None
        age_seconds = time.time() - float(entry["time"])
        return {
            "data": entry["data"],
            "stale": age_seconds > _ttl_seconds(),
            "age_seconds": age_seconds,
        }


def get_cached(ticker: str, allow_stale: bool = False) -> Any | None:
    entry = get_cached_entry(ticker)
    if not entry:
        return None
    if entry["stale"] and not allow_stale:
        return None
    return entry["data"]


def set_cached(ticker: str, data: Any) -> None:
    normalized = (ticker or "").strip().upper()
    if not normalized:
        return
    with _LOCK:
        CACHE[normalized] = {
            "data": data,
            "time": time.time(),
        }


def clear_expired() -> None:
    cutoff = time.time() - _stale_retention_seconds()
    with _LOCK:
        expired = [ticker for ticker, entry in CACHE.items() if float(entry["time"]) < cutoff]
        for ticker in expired:
            CACHE.pop(ticker, None)


def cache_size() -> int:
    with _LOCK:
        return len(CACHE)
