"""Explicit catalogue seeding: `python -m app.seed`.

Idempotent — safe to run repeatedly. Reads settings from the environment, so
production seeding is an operator action, never a side effect of booting the
app (boot-time writes would touch Firestore credentials during construction).

Usage:
    python -m app.seed            # seed interests + relationship records
"""

from __future__ import annotations

import json
import sys

from .catalogue import seed_catalogue
from .config import get_settings
from .observability import log_event
from .store import create_store


def main() -> int:
    settings = get_settings()
    store = create_store(settings)
    counts = seed_catalogue(store)
    log_event("catalogue_seeded_cli", app_mode=settings.app_mode, **counts)
    print(json.dumps({"app_mode": settings.app_mode, **counts}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
