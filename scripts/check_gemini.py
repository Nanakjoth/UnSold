"""Make ONE real Gemini call and print the honest source label (spec section 15).

CORE_REALIGNMENT "Cloud enablement": verify the live path actually works once
credentials are present, without ever faking a call. This script:

  * loads configuration from the environment (same `Settings` the app uses),
  * refuses to pretend: if the env is not really configured it says so and exits,
  * otherwise makes a single structured call through the app's own GeminiClient
    and prints whether the result came from `gemini` or the `fallback`.

Run it after `gcloud auth application-default login` (or on Cloud Run with its
attached identity) and after setting GOOGLE_CLOUD_PROJECT / GOOGLE_CLOUD_LOCATION /
GEMINI_MODEL / EMBED_MODEL / EMBED_DIM.

Usage:
    server\\.venv\\Scripts\\python scripts\\check_gemini.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from app.config import get_settings  # noqa: E402
from app.gemini import create_gemini  # noqa: E402
from app.models import GuardianVerdict  # noqa: E402


def main() -> int:
    settings = get_settings()

    print("Gemini connectivity check")
    print(f"  APP_MODE               : {settings.app_mode}")
    print(f"  GOOGLE_CLOUD_PROJECT   : {settings.google_cloud_project}")
    print(f"  GOOGLE_CLOUD_LOCATION  : {settings.google_cloud_location}")
    print(f"  GEMINI_MODEL           : {settings.gemini_model}")
    print(f"  EMBED_MODEL            : {settings.embed_model}")
    print(f"  EMBED_DIM              : {settings.embed_dim}")
    print(f"  cloud_configured       : {settings.cloud_configured}")

    client = create_gemini(settings)
    if client is None:
        print(
            "\nRESULT: fallback — the environment is not fully configured, so no "
            "live call was attempted. Set the GOOGLE_CLOUD_*/GEMINI_*/EMBED_* "
            "variables (and authenticate) to exercise the live path."
        )
        return 2

    # One small, structured call through the app's own prompt + schema path.
    print("\nMaking one structured call via prompts/guardian.md ...")
    result = client.structured(
        "guardian",
        {"text": "Enroll now in my course at Brightpath Academy — limited seats!", "sender_role": "mentor"},
        GuardianVerdict,
    )

    print(f"  source   : {result.source}")
    print(f"  degraded : {result.degraded}")
    if result.error_category:
        print(f"  error    : {result.error_category}")
    if result.data is not None:
        verdict: GuardianVerdict = result.data
        print(f"  is_pitch : {verdict.is_pitch}")
        print(f"  category : {verdict.category}")
        print(f"  severity : {verdict.severity}")

    if result.source == "gemini":
        print("\nRESULT: gemini — a real live model produced this. Honest label confirmed.")
        return 0

    print(
        "\nRESULT: fallback — the live call did not succeed (see error above). The app "
        "correctly fell back to its deterministic classifier rather than pretending."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
