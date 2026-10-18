"""Structured, content-free application logging.

Every event is a single JSON line. Values are IDs, enums, counts, latencies,
and status flags only — never message text, prompts, PII, or contact values
(product spec section 15). Long free-text values are truncated defensively so a
buggy call site cannot dump user content into the logs.
"""

from __future__ import annotations

import json
import sys
import time
import uuid
from typing import Any

# Anything longer than this in a log value is almost certainly content, not metadata.
_MAX_VALUE_CHARS = 120


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def _safe(value: Any) -> Any:
    if isinstance(value, str) and len(value) > _MAX_VALUE_CHARS:
        return f"[truncated:{len(value)}chars]"
    return value


def log_event(event: str, *, request_id: str | None = None, **fields: Any) -> None:
    """Emit one structured event line. ``event`` and fields must be content-free."""
    record: dict[str, Any] = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "event": event,
    }
    if request_id is not None:
        record["request_id"] = request_id
    record.update({key: _safe(value) for key, value in fields.items()})
    print(json.dumps(record, sort_keys=True, default=str), file=sys.stdout, flush=True)
