"""Small in-memory cache helpers for Startup Hub service responses."""

from __future__ import annotations

import threading
import time
from copy import deepcopy
from typing import Any

_LOCK = threading.Lock()
_CACHE: dict[str, dict[str, Any]] = {}


def build_cache_key(namespace: str, **parts: Any) -> str:
    serialized_parts: list[str] = []
    for key in sorted(parts):
        value = parts[key]
        serialized_parts.append(f"{key}={value if value is not None else 'none'}")
    suffix = "|".join(serialized_parts)
    return f"{namespace}|{suffix}" if suffix else namespace


def get_cache_entry(key: str, *, allow_stale: bool = True) -> dict[str, Any] | None:
    with _LOCK:
        entry = _CACHE.get(key)
        if entry is None:
            return None

        age_seconds = max(time.time() - float(entry["time"]), 0.0)
        ttl_seconds = max(float(entry["ttl_seconds"]), 0.0)
        is_stale = age_seconds >= ttl_seconds if ttl_seconds else False

        if is_stale and not allow_stale:
            _CACHE.pop(key, None)
            return None

        return {
            "key": key,
            "payload": deepcopy(entry["payload"]),
            "time": entry["time"],
            "ttl_seconds": ttl_seconds,
            "age_seconds": round(age_seconds, 2),
            "is_stale": is_stale,
        }


def set_cache_entry(key: str, value: Any, ttl_seconds: int | float) -> dict[str, Any]:
    stored = {
        "payload": deepcopy(value),
        "time": time.time(),
        "ttl_seconds": float(ttl_seconds),
    }
    with _LOCK:
        _CACHE[key] = stored
    return {
        "key": key,
        "payload": deepcopy(value),
        "time": stored["time"],
        "ttl_seconds": float(ttl_seconds),
        "age_seconds": 0.0,
        "is_stale": False,
    }


def invalidate_cache(prefix: str | None = None) -> int:
    with _LOCK:
        if prefix is None:
            count = len(_CACHE)
            _CACHE.clear()
            return count

        matching_keys = [key for key in _CACHE if key.startswith(prefix)]
        for key in matching_keys:
            _CACHE.pop(key, None)
        return len(matching_keys)


def get_cached_payload(key: str, *, allow_stale: bool = True) -> dict[str, Any] | None:
    return get_cache_entry(key, allow_stale=allow_stale)


def set_cached_payload(key: str, value: Any, ttl_seconds: int | float) -> dict[str, Any]:
    return set_cache_entry(key, value, ttl_seconds)

