"""Per-user and per-IP rate limiting (spec section 9).

A small sliding-window limiter keyed by caller identity (authenticated uid when
available, otherwise client IP). Conservative defaults; counts are logged, keys
are never logged with message content.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request
from starlette.responses import JSONResponse

from .observability import log_event


class RateLimiter:
    """Sliding-window limiter. In-memory and per-process — honest about it.

    For the prototype (single Cloud Run instance in demo, or a small number of
    instances) an in-process window is adequate. A distributed limiter is only
    justified when measured traffic requires it.
    """

    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str) -> bool:
        """Record a hit for `key`; return False when the caller is over limit."""
        now = time.monotonic()
        window_start = now - 60.0
        with self._lock:
            bucket = self._hits[key]
            while bucket and bucket[0] < window_start:
                bucket.popleft()
            if len(bucket) >= self.per_minute:
                return False
            bucket.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


def caller_key(request: Request) -> str:
    """Best available caller identity: verified uid, else client IP."""
    uid = getattr(request.state, "uid", None)
    if uid:
        return f"uid:{uid}"
    host = request.client.host if request.client else "unknown"
    return f"ip:{host}"


def rate_limit_response() -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={
            "error": {
                "code": "rate_limited",
                "message": "Too many requests. Wait a moment and try again.",
            }
        },
        headers={"Retry-After": "60"},
    )


async def enforce_rate_limit(request: Request) -> None:
    """FastAPI dependency: raise a 429 for callers over their limit."""
    limiter: RateLimiter | None = getattr(request.app.state, "rate_limiter", None)
    if limiter is None:  # pragma: no cover - misconfiguration guard
        return
    key = caller_key(request)
    if not limiter.check(key):
        log_event("rate_limited", key=key, path=request.url.path)
        raise _RateLimited()


class _RateLimited(Exception):
    pass
